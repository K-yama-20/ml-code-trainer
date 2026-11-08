"""Export all 180 interface decisions without exposing fixtures or answers."""
import collections
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "content/compiled/private.json").read_text(encoding="utf-8"))
    rows = []
    for p in data["problems"]:
        workspace = p["workspace"]
        mode = workspace["mode"]
        technical = bool(re.search(r"NCHW|BCE|stride|one.hot|state_dict|map_location|stratify|勾配|リーク", workspace["task"]))
        rows.append({
            "id": p["id"], "version": p["version_id"], "module": p["module_id"], "stage": p["stage"], "type": p["type"],
            "input": "具体的な公開入力をコード表示", "mode": mode, "structure": workspace["structure"],
            "reason": workspace["classification_reason"],
            "previous_editor": "固定値欄と複数入力に応じる式が混在" if mode == "prediction" else "提供入力が解答と分離されず、solve全体を編集",
            "abstract_copy": "具体例と説明を詳細改稿" if workspace["authored"] else "専門用語の理解を要人手確認" if technical else "旧本文を基本維持。説明の十分さを要人手確認",
            "output_example": "正解を初期表示しない" if mode == "prediction" else "具体入力に対応する例が必要。公開ケースで照合済み",
            "grading": "固定観察1ケース" if mode == "prediction" else "関数入口を具体名へ変更。戻り値採点を維持" if mode == "function" else "提供入力を注入しresultを採点。異なる値・shapeと入力保護を検証",
            "editorial_review": "今回の詳細改稿15問" if workspace["authored"] else "詳細な教材改稿は未完了",
        })
    counts = collections.Counter(r["mode"] for r in rows)
    header = """# 全180問の問題形式・移行判断

この表はコード・問題定義・模範解答・採点ケースから確認した構造の分類である。「説明の十分さ」は初学者テストで確認する仮説として残す。全180問で具体入力workspaceを導入したが、今回の詳細改稿は15問。他165問の日本語・ヒント・解説を全面的に書き直したという意味ではない。

入力は全180問で具体表示。156問はscript（うち3問はクラスとメソッドを保持）、4問は引数や関数の学習のため関数を維持、20問は固定コードの出力予測。全問の模範解答と表示入力の一致を検証する。全体の難易度・concept・family・3段階の構成は維持する。

旧解答欄は基本操作にも採点用のsolve全体を要求し、具体入力が同じコード面にない。出力予測は固定値と汎用式の要求が混在していた。現在の編集対象、抽象表現の残存、期待出力例、採点変更を各行に記載する。型・shape・index・APIの意味が初心者に伝わるかは、表の合格だけでは判断しない。

| 問題 | 分野 / 段階 / 形式 | 入力・維持する構造 | 旧欄の評価 / 変更 | 文章・例の確認 | 採点の変更 | 詳細改稿 |
|---|---|---|---|---|---|---|
"""
    lines = [header]
    for r in rows:
        lines.append(f"| {r['id']} | {r['module']} / {r['stage']} / {r['type']} | 具体入力 / {r['structure']}：{r['reason']} | {r['previous_editor']} → {r['mode']} | {r['abstract_copy']}。{r['output_example']} | {r['grading']} | {r['editorial_review']} |")
    (ROOT / "docs/DRILL_PROBLEM_CLASSIFICATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "docs/drill_problem_classification.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(dict(counts))


if __name__ == "__main__":
    main()
