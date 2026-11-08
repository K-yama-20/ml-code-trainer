from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem
from apps.api.app.grading import judge
from content.arguments import LESSONS
from content.runner import run_payload
from scripts.validate_content import check_display, check_reference


def test_argument_lessons_and_reference_answers():
    assert len(LESSONS) == 18
    assert [lesson["number"] for lesson in LESSONS] == list(range(1, 19))
    for seed, data in VARIANTS.items():
        questions = [p for p in data["problems"] if p["concept_id"] == "PY02"]
        assert len({p["id"] for p in data["problems"]}) == len(data["problems"])
        assert [p["id"] for p in questions] == [lesson["id"] for lesson in LESSONS]
        for p, lesson in zip(questions, LESSONS, strict=True):
            assert p["title"] == lesson["title"]
            assert p["description"] == lesson["task"]
            assert p["hints"] == [lesson["hint"]]
            assert p["solution"] == lesson["solution"]
            workspace = p["workspace"]
            starter = p["starter_code"]
            invocation = workspace["invocation"]
            prefix = workspace["provided_code"]
            if prefix:
                prefix += "\n\n" if workspace["mode"] == "function" and starter else "\n"
            suffix = ("\n\n" if starter else "\n") + invocation if invocation else ""
            assert (prefix + starter.rstrip() + suffix) == lesson["starter"]
            assert p["editable_regions"] == [{"start": len(starter), "end": len(starter)}]
            assert lesson["solution"].startswith(starter)
            assert lesson["solution"][len(starter) :].strip()
            check_display(p)
            result = check_reference(p)
            assert result["verdict"] == "Accepted" and result["passed_tests"] == 4, result
            expected = lesson["expected"]
            code = f"result = {expected!r}"
            if invocation:
                signature = p["solution"].splitlines()[0]
                code = f"{signature}\n    return {expected!r}"
            cases = p["public_tests"] + p["hidden_tests"]
            outputs = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
            assert judge(outputs["outputs"], cases, code, p["required_ast"])["verdict"] != "Accepted", p["id"]
            if p["content_version"] > 1:
                old = ARCHIVED_VARIANTS[(f"{p['id']}@{p['content_version'] - 1}", seed)]
                assert problem(old["version_id"], seed) == old
                assert old["family_id"] == p["family_id"] and old["stage"] == p["stage"]


def test_argument_checks_accept_alternatives_and_reject_incorrect_styles():
    examples = [
        (1, "result = 14", False),
        (1, "result = transform(scale, x, bias)", False),
        (2, "result = clip(x, lower, upper)", False),
        (2, "result = clip(upper=upper, x=x, lower=lower)", True),
        (2, "call = clip\nresult = call(upper=upper, x=x, lower=lower)", True),
        (3, "result = predict(x, weight, bias)", False),
        (4, "result = scale_values(values, factor=2)", False),
        (5, "result = scale_values(values, 3)", True),
        (6, "result = normalize_score(score, divisor=100, offset=0.1)", False),
        (8, "def average_loss(*values):\n    return 0.4", False),
        (8, "def average_loss(*values):\n    return sum(values) / len(values)", True),
        (10, "def get_lr(**params):\n    return params.get('lr', 0.01)", False),
        (11, "def count_enabled(**options):\n    return len([v for v in options.values() if v])", True),
        (13, "result = weighted_sum(features[0], features[1], features[2])", False),
        (15, "result = mean_of_four(*second, *first)", False),
        (15, "result = mean_of_four(*(first + second))", True),
        (16, "result = training_summary(lr=config['lr'], batch_size=config['batch_size'])", False),
        (18, "def call_metric(fn, *args, **kwargs):\n    return fn(*args)", False),
        (18, "def call_metric(fn, *args, **kwargs):\n    return fn(*tuple(args), **dict(kwargs))", True),
    ]
    for number, code, accepted in examples:
        p = problem(LESSONS[number - 1]["id"])
        cases = p["public_tests"] + p["hidden_tests"]
        out = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
        result = judge(out["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
        assert (result["verdict"] == "Accepted") == accepted, (number, code, result)
