from datetime import timedelta, timezone
import random
from sqlalchemy import select
from .db import Attempt, ConceptProgress, ProblemProgress, Review, StudySession, now
from .content import DATA, CONCEPTS, VERSIONS, problem
from .config import settings

INTERVALS = [1, 3, 7, 14, 30]


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def update_learning(db, user_id, item, attempt):
    p = problem(item.problem_version_id, item.variant_seed)
    cid = p["concept_id"]
    progress = db.get(ConceptProgress, (user_id, cid))
    if not progress:
        progress = ConceptProgress(user_id=user_id, concept_id=cid, stage_families={}, mastery_level=0)
        db.add(progress)
    review = db.get(Review, (user_id, cid))
    was_due = review is not None and aware(review.due_at) <= now()
    clean = attempt.verdict == "Accepted" and attempt.hint_level_used == 0 and not attempt.solution_viewed
    verified = attempt.verification_level == "server_verified"
    problem_progress = db.get(ProblemProgress, (user_id, attempt.problem_version_id))
    if not problem_progress:
        problem_progress = ProblemProgress(user_id=user_id, problem_version_id=attempt.problem_version_id, data={})
        db.add(problem_progress)
    previous = problem_progress.data or {}
    problem_progress.data = {
        "attempts": previous.get("attempts", 0) + 1,
        "accepted": previous.get("accepted", 0) + int(attempt.verdict == "Accepted"),
        "verified_clean": previous.get("verified_clean", False) or (verified and clean),
        "last_verdict": attempt.verdict,
        "last_seed": attempt.variant_seed,
        "last_practiced_at": now().isoformat(),
    }
    families = {k: list(v) for k, v in (progress.stage_families or {}).items()}
    if clean:
        key = p["stage"]
        if key != "independent" or verified:
            families[key] = list(set(families.get(key, []) + [p["id"]]))
        if key == "independent" and not verified:
            families["independent_provisional"] = list(set(families.get("independent_provisional", []) + [p["id"]]))
    progress.stage_families = families
    level = 0
    for stage in ("guided", "partial", "independent"):
        if len(families.get(stage, [])) >= 2:
            level += 1
        else:
            break
    if level >= 3 and verified and clean:
        prior = (
            db.query(Attempt)
            .filter(
                Attempt.user_id == user_id,
                Attempt.id != attempt.id,
                Attempt.verification_level == "server_verified",
                Attempt.verdict == "Accepted",
                Attempt.problem_version_id.in_([p["version_id"] for p in VERSIONS.values() if p["concept_id"] == cid]),
            )
            .all()
        )
        if any(a.variant_seed != attempt.variant_seed for a in prior):
            level = 4
        if was_due and review and review.success_streak >= 2:
            level = 5
    progress.mastery_level = max(progress.mastery_level or 0, level)
    # Score describes confidence; stage certification still uses the exact gates.
    quality = (p["difficulty"] / 3) / (1 + 0.1 * max(0, attempt.run_count - 1))
    quality *= 1 if previous.get("attempts", 0) == 0 else 0.8
    quality *= 1 if clean else 0.4 if attempt.verdict == "Accepted" else 0
    progress.mastery_score = max(
        0, min(1, progress.mastery_level / 5 + quality * 0.05 - (0.05 if attempt.verdict != "Accepted" else 0))
    )
    progress.current_stage = "guided" if level < 1 else "partial" if level < 2 else "independent"
    progress.last_practiced_at = now()
    if verified:
        progress.last_verified_at = now()
    if not review:
        review = Review(
            user_id=user_id,
            concept_id=cid,
            due_at=now() + timedelta(days=1),
            interval_days=1,
            success_streak=0,
            last_problem_family_id=p["id"],
        )
        db.add(review)
    # Repeated same-day attempts cannot push a due date out indefinitely.
    if was_due or attempt.verdict != "Accepted":
        streak = min((review.success_streak or 0) + 1, 4) if clean else 0
        review.success_streak = streak
        review.interval_days = INTERVALS[streak] if clean else 1
        review.due_at = now() + timedelta(days=review.interval_days)
        review.last_reviewed_at = now()
    review.last_problem_family_id = p["id"]
    item.completed = attempt.verdict == "Accepted"
    session = db.get(StudySession, item.session_id)
    session.position = item.position
    session.updated_at = now()


def choose_queue(db, user_id, request):
    progress = {p.concept_id: p for p in db.scalars(select(ConceptProgress).where(ConceptProgress.user_id == user_id))}
    reviews = list(db.scalars(select(Review).where(Review.user_id == user_id, Review.due_at <= now())))
    due = {r.concept_id: r for r in reviews}
    pool = [
        p
        for p in DATA["problems"]
        if (not request.concept_id or p["concept_id"] == request.concept_id)
        and (not request.modules or p["module_id"] in request.modules)
        and (not request.stages or p["stage"] in request.stages)
    ]
    if request.kind in ("concept", "custom") and CONCEPTS.get(request.concept_id, {}).get("ordered_practice"):
        return pool[: request.count]
    ordered_candidates = pool
    if request.kind in ("daily", "concept", "review") and not (request.kind == "concept" and request.stages):
        pool = [
            p
            for p in pool
            if p["stage"] == (progress[p["concept_id"]].current_stage if p["concept_id"] in progress else "guided")
        ]
    if request.kind == "daily" and not settings.modal_ready:
        pool = [p for p in pool if p["runtime"] == "browser"]
    if request.kind == "review":
        pool = [p for p in pool if p["concept_id"] in due]
    rng = random.Random(f"{user_id}:{now().date()}:{request.kind}")
    rng.shuffle(pool)
    due_pool = [p for p in pool if p["concept_id"] in due]
    new_pool = [p for p in pool if p["concept_id"] not in progress]
    weak_pool = [p for p in pool if p["concept_id"] in progress and p["concept_id"] not in due]
    if request.kind == "daily":
        queue = (
            due_pool[: round(request.count * 0.4)]
            + new_pool[: round(request.count * 0.4)]
            + weak_pool[: round(request.count * 0.2)]
        )
        chosen = {p["id"] for p in queue}
        queue += [p for p in pool if p["id"] not in chosen]
    else:
        queue = pool
    # Prefer the other family on review; variants alternate by last seed.
    queue.sort(key=lambda p: p["concept_id"] in due and due[p["concept_id"]].last_problem_family_id == p["id"])
    if request.kind == "daily":
        # count is a goal, not a queue boundary. Start with one coherent stage.
        eligible = [
            p for p in pool if all(cid in progress and progress[cid].mastery_level >= 1 for cid in p["prerequisites"])
        ]
        focus = (
            min(
                eligible or pool,
                key=lambda p: (
                    p["concept_id"] not in due,
                    CONCEPTS[p["concept_id"]]["order"],
                    p["id"],
                ),
            )
            if pool
            else None
        )
        if focus and CONCEPTS[focus["concept_id"]].get("ordered_practice"):
            return [p for p in ordered_candidates if p["concept_id"] == focus["concept_id"]][:2]
        return sorted([p for p in pool if focus and p["concept_id"] == focus["concept_id"]], key=lambda p: p["id"])[:2]
    return queue[: request.count]


def continuation_queue(db, user_id, session, policy, previous, items):
    """Select more practice, without changing certification or an existing queue."""
    progress = {p.concept_id: p for p in db.scalars(select(ConceptProgress).where(ConceptProgress.user_id == user_id))}
    due = {r.concept_id for r in db.scalars(select(Review).where(Review.user_id == user_id, Review.due_at <= now()))}
    modules = policy.get("modules", [])
    progressive = session.kind != "custom" or policy.get("legacy_progressive", False)
    stages = [] if progressive else policy.get("stages", [])
    pool = [
        p
        for p in DATA["problems"]
        if (not modules or p["module_id"] in modules)
        and (not stages or p["stage"] in stages)
        and (not (not progressive and policy.get("concept_id")) or p["concept_id"] == policy["concept_id"])
        and (p["runtime"] == "browser" or settings.modal_ready)
    ]
    if not pool:
        return (
            [],
            "この範囲には、現在の環境で実行できる問題がありません。別の分野を選ぶか、実行環境の準備後に再開してください。",
        )
    current = problem(previous.problem_version_id, previous.variant_seed)
    cid = current["concept_id"]
    ordered_candidates = pool
    if session.kind != "review" and CONCEPTS[cid].get("ordered_practice"):
        queued = {item.problem_version_id.split("@")[0] for item in items}
        requested_stages = policy.get("stages", [])
        if session.kind == "concept" and requested_stages:
            stages_in_order = ("guided", "partial", "independent")
            first = problem(items[0].problem_version_id, items[0].variant_seed)
            requested_stages = stages_in_order[stages_in_order.index(first["stage"]):]
        pending = [
            p for p in pool
            if p["concept_id"] == cid and p["id"] not in queued
            and (not requested_stages or p["stage"] in requested_stages)
        ]
        if pending:
            return pending[:2], ""
    # Explicit custom filters are a practice scope, not an implicit certification.
    practiced = {}
    for item in items:
        p = problem(item.problem_version_id, item.variant_seed)
        if item.completed and p and p["stage"] == "independent":
            practiced.setdefault(p["concept_id"], set()).add(p["family_id"])

    def practice_finished(concept_id):
        return (concept_id in progress and progress[concept_id].mastery_level >= 3) or len(
            practiced.get(concept_id, set())
        ) >= 2

    if not stages:

        def practice_stage(concept_id):
            if progressive and concept_id == cid:
                # A deliberately selected starting stage is respected. This
                # changes practice order, never the certification prerequisites.
                stage = current["stage"]
                families = progress[cid].stage_families if cid in progress else {}
                if stage != "independent" and len(families.get(stage, [])) >= 2:
                    return "partial" if stage == "guided" else "independent"
                return stage
            return progress[concept_id].current_stage if concept_id in progress else "guided"

        pool = [p for p in pool if p["stage"] == practice_stage(p["concept_id"])]
    same = [p for p in pool if p["concept_id"] == cid]
    if same and (stages or not practice_finished(cid)):
        selected = same
    else:
        candidates = [p for p in pool if p["concept_id"] != cid and not practice_finished(p["concept_id"])]
        eligible = [
            p
            for p in candidates
            if all(pre in progress and progress[pre].mastery_level >= 1 for pre in p["prerequisites"])
        ]
        candidates = eligible or candidates or pool
        if not candidates:
            return [], "この条件で続けられる問題がありません。分野やステージを変えて続けられます。"
        target = min(
            candidates,
            key=lambda p: (
                p["concept_id"] not in due,
                cid not in p["prerequisites"],
                p["module_id"] != current["module_id"],
                CONCEPTS[p["concept_id"]]["order"],
                p["id"],
            ),
        )["concept_id"]
        selected = [p for p in pool if p["concept_id"] == target]
    target_id = selected[0]["concept_id"]
    if CONCEPTS[target_id].get("ordered_practice"):
        if target_id != cid and session.kind != "review" and not policy.get("stages"):
            selected = [p for p in ordered_candidates if p["concept_id"] == target_id]
    else:
        selected.sort(key=lambda p: p["id"])
    target = selected[0]
    if target["concept_id"] != cid:
        message = f"続いて「{CONCEPTS[target['concept_id']]['title']}」を練習します。"
    elif target["stage"] != current["stage"]:
        label = {"guided": "穴埋め", "partial": "部分記述", "independent": "補助なしの練習"}[target["stage"]]
        message = f"次は{label}へ進みます。"
    else:
        message = "もう一度、ヒントなしで確かめましょう。前の練習の記録はそのまま残ります。"
    return selected[:2], message
