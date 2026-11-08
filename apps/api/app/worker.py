"""Run independently: python -m apps.api.app.worker. Durable leases and cancellation."""

from datetime import timedelta
import logging
import threading
import time
from sqlalchemy import select, update
from .config import settings
from .content import problem
from .db import Job, SessionItem, SessionLocal, init_db, now
from .execution import ModalProvider
from .grading import judge

log = logging.getLogger(__name__)


def run_problem(provider, p, code, submit, created):
    """Public and private inputs never share a learner process or output stream."""
    batches = [p["public_tests"]]
    if submit and p["hidden_tests"]:
        batches.append(p["hidden_tests"])
    combined = {"outputs": [], "stdout": ""}
    for index, cases in enumerate(batches):
        payload = {
            "code": code,
            "cases": [{"setup": c["setup"], "args": c["args"]} for c in cases],
            "execution": p.get("execution", {}),
        }
        sid = provider.create_execution(payload, created)
        output = provider.get_execution_result(sid)
        combined["outputs"].extend(output["outputs"])
        if index == 0:
            combined["stdout"] = output.get("stdout", "")[:32768]
    return combined


def recover_expired(db):
    db.execute(
        update(Job)
        .where(Job.status == "running", Job.lease_until < now())
        .values(
            status="failed",
            finished_at=now(),
            result={
                "verdict": "System Error",
                "passed_tests": 0,
                "total_tests": 0,
                "stderr": "Worker lease expired. Submit again with a new request ID.",
            },
        )
    )
    db.execute(
        update(Job)
        .where(Job.status == "queued", Job.created_at < now() - timedelta(minutes=5))
        .values(
            status="failed",
            finished_at=now(),
            result={
                "verdict": "Execution Failed",
                "passed_tests": 0,
                "total_tests": 0,
                "stderr": "Queue wait limit exceeded",
            },
        )
    )
    db.commit()


def claim(db):
    recover_expired(db)
    id = db.scalar(select(Job.id).where(Job.status == "queued").order_by(Job.created_at).limit(1))
    if not id:
        return None
    changed = db.execute(
        update(Job)
        .where(Job.id == id, Job.status == "queued")
        .values(status="running", started_at=now(), lease_until=now() + timedelta(seconds=90))
    ).rowcount
    db.commit()
    return id if changed == 1 else None


def execute_job(provider, id):
    stop = threading.Event()

    def heartbeat():
        while not stop.wait(2):
            with SessionLocal() as db:
                job = db.get(Job, id)
                if job.status == "cancelled":
                    if job.provider_id:
                        try:
                            provider.cancel_execution(job.provider_id)
                        except Exception:
                            log.exception("Sandbox cancellation failed")
                    return
                job.lease_until = now() + timedelta(seconds=90)
                db.commit()

    threading.Thread(target=heartbeat, daemon=True).start()
    started = time.monotonic()
    try:
        with SessionLocal() as db:
            job = db.get(Job, id)
            item = db.get(SessionItem, job.item_id)
            p = problem(job.problem_version_id, item.variant_seed)
            cases = p["public_tests"] + (p["hidden_tests"] if job.mode == "submit" else [])
            # Only code and inputs enter the untrusted environment.
            code = job.code
            submit = job.mode == "submit"

        def created(sandbox_id):
            with SessionLocal() as db:
                if db.get(Job, id).status == "cancelled":
                    provider.cancel_execution(sandbox_id)
                    raise InterruptedError("Cancelled before the next sandbox started")
                db.execute(update(Job).where(Job.id == id).values(provider_id=sandbox_id))
                db.commit()

        output = run_problem(provider, p, code, submit, created)
        result = judge(
            output["outputs"],
            cases,
            code,
            p["required_ast"],
            p["check_dtype"],
            p.get("protect_inputs", False),
            len(p["public_tests"]),
        )
        # Do not return hidden individual test errors or values.
        result["tests"] = result["tests"][: len(p["public_tests"])]
        if not any("error" in o for o in output["outputs"][: len(p["public_tests"])]) and any(
            "error" in o for o in output["outputs"][len(p["public_tests"]) :]
        ):
            result["stderr"] = (
                "表示例とは異なる入力でエラーになりました。入力の大きさや値に依存する箇所を見直してください。"
            )
            result["error_line"] = None
        result["stdout"] = output.get("stdout", "")[:32768]
        result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
        status = "completed"
    except TimeoutError:
        result = {
            "verdict": "Time Limit Exceeded",
            "passed_tests": 0,
            "total_tests": 0,
            "stderr": "30秒の実行上限を超えました。",
        }
        status = "timed_out"
    except Exception:
        log.exception("Execution failed for %s", id)
        result = {
            "verdict": "Execution Failed",
            "passed_tests": 0,
            "total_tests": 0,
            "stderr": "Sandboxの起動または実行に失敗しました。",
        }
        status = "failed"
    finally:
        stop.set()
    with SessionLocal() as db:
        db.execute(
            update(Job)
            .where(Job.id == id, Job.status == "running")
            .values(status=status, result=result, finished_at=now(), lease_until=None)
        )
        db.commit()


def main():
    if not settings.modal_ready:
        raise SystemExit("EXECUTION_PROVIDER=modal must be configured; no fallback executes learner code locally.")
    init_db()
    provider = ModalProvider()
    while True:
        with SessionLocal() as db:
            id = claim(db)
        if id:
            execute_job(provider, id)
        else:
            time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
