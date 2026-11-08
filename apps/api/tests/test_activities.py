from pathlib import Path
import subprocess
import sys
import tempfile
import pytest
from content.activities import DEEP_DIVES, READING_META, READING_QUESTIONS

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("task", DEEP_DIVES, ids=lambda t: t["id"])
def test_deep_dive_answers(client, task):
    data = client.get("/api/v1/deep-dives/" + task["id"]).json()
    assert len(data["flow"]) == 3 and data["code"]
    q = task["questions"][0]
    assert "answer" not in data["questions"][0]
    assert (
        client.post(
            f"/api/v1/activities/{task['id']}/answers",
            json={"question_id": q["id"], "answer": (q["answer"] + 1) % len(q["choices"])},
        ).json()["accepted"]
        is False
    )
    assert (
        client.post(
            f"/api/v1/activities/{task['id']}/answers", json={"question_id": q["id"], "answer": q["answer"]}
        ).json()["accepted"]
        is True
    )


@pytest.mark.parametrize("meta", READING_META, ids=lambda m: m["id"])
def test_reading_questions(client, meta):
    data = client.get("/api/v1/reading-projects/" + meta["id"]).json()
    assert len(data["questions"]) == 8
    for q in READING_QUESTIONS[meta["id"]]:
        assert (
            client.post(
                f"/api/v1/activities/{meta['id']}/answers", json={"question_id": q["id"], "answer": q["answer"]}
            ).json()["accepted"]
            is True
        )


@pytest.mark.parametrize("meta", READING_META, ids=lambda m: m["id"])
def test_reading_projects_execute(meta):
    # Only repository-authored sample code, never user input.
    project = ROOT / "content/reading" / meta["id"]
    with tempfile.TemporaryDirectory() as out:
        command = [sys.executable, str(project / meta["entry"]), "--output", out]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr
        if meta["id"] == "pytorch-training":
            result = subprocess.run(
                [sys.executable, str(project / "inference.py"), str(Path(out) / "model.pt")],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr
