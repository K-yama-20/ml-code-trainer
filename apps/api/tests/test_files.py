from pathlib import Path

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem
from apps.api.app.grading import judge
from content.files import LESSONS
from content.runner import pack, run_payload
from scripts.validate_content import check_display, check_reference


def evaluate(p, code):
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    return judge(output["outputs"], cases, code, p["required_ast"], True, True)


def test_files_match_the_authored_copy_and_execute_with_isolated_fixtures():
    assert len(LESSONS) == 18
    assert [lesson["number"] for lesson in LESSONS] == list(range(1, 19))
    for seed, data in VARIANTS.items():
        questions = [p for p in data["problems"] if p["concept_id"] == "PY03"]
        assert len({p["id"] for p in data["problems"]}) == len(data["problems"])
        assert [p["id"] for p in questions] == [lesson["id"] for lesson in LESSONS]
        for p, lesson in zip(questions, LESSONS, strict=True):
            assert p["title"] == lesson["title"]
            assert p["description"] == lesson["task"]
            assert p["hints"] == [lesson["hint"]]
            assert p["solution"] == lesson["solution"]
            assert p["public_tests"][0]["expected"] == lesson["expected"]
            starter = p["starter_code"]
            invocation = p["workspace"]["invocation"]
            suffix = "\n" + invocation if invocation else ""
            assert p["workspace"]["provided_code"] + "\n" + starter.rstrip() + suffix == lesson["starter"]
            assert p["editable_regions"] == [{"start": len(starter), "end": len(starter)}]
            assert p["solution"].startswith(starter)
            check_display(p)
            assert check_reference(p)["verdict"] == "Accepted", p["id"]
            # Repeat an append without carrying over the previous file state.
            if lesson["number"] == 17:
                assert check_reference(p)["verdict"] == "Accepted"
            if p["content_version"] > 1:
                old = ARCHIVED_VARIANTS[(f"{p['id']}@{p['content_version'] - 1}", seed)]
                assert problem(old["version_id"], seed) == old
                assert old["stage"] == p["stage"]


def test_file_outputs_formats_and_valid_alternatives():
    examples = [
        (1, 'result = ".csv"', False),
        (4, 'result = "dataset/train/images.csv"', False),
        (4, "result = root.joinpath(split, filename)", True),
        (6, 'result = path.with_name(path.stem + "_backup" + path.suffix)', True),
        (9, 'result = list(map(lambda item: item["loss"], json.loads(text)))', False),
        (10, "result = json.dumps(config, sort_keys=True, indent=4)", True),
        (10, "result = config", False),
        (11, "result = json.dumps(config)", False),
        (11, "result = json.dumps(config, sort_keys=True, indent=2, ensure_ascii=False)", True),
        (12, "result = json.dumps(config, sort_keys=True)", False),
        (12, "result = json.dumps(config, indent=4, sort_keys=True)", False),
        (12, "result = json.dumps(config, indent=2)", False),
        (14, 'result = path.read_text(encoding="utf-8").strip().splitlines()', False),
        (15, 'with path.open(encoding="utf-8") as f:\n    result = json.load(f)', True),
        (16, 'result = "accuracy=0.91\\n"', False),
        (17, 'path.write_text(new_line, encoding="utf-8")', False),
        (17, 'path.write_text(path.read_text(encoding="utf-8") + new_line, encoding="utf-8")', True),
        (18, "result = config", False),
        (18, 'path.write_text(json.dumps(config), encoding="utf-8")', False),
    ]
    for number, code, accepted in examples:
        p = problem(LESSONS[number - 1]["id"])
        verdict = evaluate(p, code)["verdict"]
        assert (verdict == "Accepted") == accepted, (number, code, verdict)


def test_file_case_cleanup_even_on_python_errors():
    p = problem(LESSONS[16]["id"])
    result = run_payload(
        {
            "code": "raise RuntimeError(str(path.parent))",
            "cases": p["public_tests"],
            "execution": p["execution"],
        }
    )
    for output in result["outputs"]:
        assert output["kind"] == "RuntimeError"
        assert not Path(output["error"]).exists()
    assert pack(Path("dataset/train.csv")) == {"kind": "path", "value": "dataset/train.csv"}


def test_files_api_order_and_single_hint(client):
    concept = client.get("/api/v1/concepts/PY03").json()
    assert concept["problem_count"] == 18
    assert [p["id"] for p in concept["problems"]] == [lesson["id"] for lesson in LESSONS]
    session = client.post(
        "/api/v1/sessions",
        json={
            "kind": "concept",
            "concept_id": "PY03",
            "count": 18,
        },
    ).json()
    assert [p["problem_version_id"].split("@")[0] for p in session["items"]] == [lesson["id"] for lesson in LESSONS]
    item = session["items"][0]
    hint = client.post(f"/api/v1/session-items/{item['id']}/hints/2/reveal").json()
    assert hint == {"level": 1, "hints": [LESSONS[0]["hint"]]}
    assert not {"hidden_tests", "hints", "solution"} & concept["problems"][0].keys()
