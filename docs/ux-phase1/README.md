# Drill Phase 1 画面記録

[実装報告へ戻る](../UX_PHASE1_REPORT.md)

開発用の別DB・ゲストで取得した実画面。予測やコードの正誤は実API・Pyodideを用いて確認した。

## 主な変更前後

| 場面 | 変更前 | 変更後 |
|---|---|---|
| PCの問題画面 | [旧画面](before-drill-desktop.png) | [新画面](after-drill-desktop.png) |
| ヒント | [旧画面](before-hints.png) | [新画面](after-hints.png) |
| モバイル | [旧画面](before-drill-mobile.png) | [問題](after-mobile-question.png)・[回答](after-mobile-editor.png) |
| 誤答の比較 | [旧画面](../ux-audit/09-wrong-answer-no-diff.png) | [配列](after-wrong-comparison.png)・[index付き表](after-pandas-index-comparison.png) |
| 段階と継続 | [終了した旧画面](../ux-audit/08-session-ended-no-history.png) | [Partialへの進行](after-guided-to-partial.png)・[21問後](after-21-answers.png) |

## 代表15問

| 問題 | ステージ・形式 | 変更前 | 変更後 |
|---|---|---|---|
| PY01-01 正の数を選んで二乗する | guided / completion | [@1](../ux-audit/sample-PY01-01.png) | [@2](lesson-PY01-01.png) |
| PY02-06 辞書を関数の引数として渡す | independent / implementation | [@1](../ux-audit/sample-PY02-06.png) | [@2](lesson-PY02-06.png) |
| PY03-04 JSONを読み直した値を答える | partial / prediction | [@1](../ux-audit/sample-PY03-04.png) | [@2](lesson-PY03-04.png) |
| NP05-01 行ごとの平均を求める | guided / completion | [@1](../ux-audit/sample-NP05-01.png) | [@2](lesson-NP05-01.png) |
| NP06-04 2つの配列の全組合せの積を予測する | partial / prediction | [@1](../ux-audit/sample-NP06-04.png) | [@2](lesson-NP06-04.png) |
| NP09-05 学習時の平均と標準偏差で標準化する | independent / implementation | [@1](../ux-audit/sample-NP09-05.png) | [@2](lesson-NP09-05.png) |
| PD01-01 点数が5以上の行を選ぶ | guided / completion | [@1](../ux-audit/sample-PD01-01.png) | [@2](lesson-PD01-01.png) |
| PD02-04 欠損値を学習時の平均で埋める | partial / completion | [@1](../ux-audit/sample-PD02-04.png) | [@2](lesson-PD02-04.png) |
| PD04-06 右側のキーを確認して左結合する | independent / implementation | [@1](../ux-audit/sample-PD04-06.png) | [@2](lesson-PD04-06.png) |
| SK01-01 学習用とテスト用の件数を返す | guided / completion | [@1](../ux-audit/sample-SK01-01.png) | [@2](lesson-SK01-01.png) |
| SK02-04 テストを混ぜずに平均を学習する | partial / completion | [@1](../ux-audit/sample-SK02-04.png) | [@2](lesson-SK02-04.png) |
| SK03-05 学習した直線の係数を取り出す | independent / implementation | [@1](../ux-audit/sample-SK03-05.png) | [@2](lesson-SK03-05.png) |
| PT02-02 転置したTensorも1次元にする | guided / bugfix | [@1](../ux-audit/sample-PT02-02.png) | [@2](lesson-PT02-02.png) |
| PT07-04 前の勾配を消して2回更新する | partial / bugfix | [@1](../ux-audit/sample-PT07-04.png) | [@2](lesson-PT07-04.png) |
| PT10-06 復元後のモデルを推論モードにする | independent / bugfix | [@1](../ux-audit/sample-PT10-06.png) | [@2](lesson-PT10-06.png) |

## その他の記録

- [after-21-answers.png](after-21-answers.png)（1440×1000）
- [after-correct.png](after-correct.png)（1440×1000）
- [after-drill-desktop.png](after-drill-desktop.png)（1440×1000）
- [after-ended.png](after-ended.png)（1440×1000）
- [after-guided-to-partial.png](after-guided-to-partial.png)（1440×1000）
- [after-hints.png](after-hints.png)（1440×1000）
- [after-mobile-editor.png](after-mobile-editor.png)（390×845）
- [after-mobile-question.png](after-mobile-question.png)（390×845）
- [after-pandas-index-comparison.png](after-pandas-index-comparison.png)（1440×1000）
- [after-prediction-expression.png](after-prediction-expression.png)（1440×1000）
- [after-prediction-NP06-04.png](after-prediction-NP06-04.png)（1440×1000）
- [after-prediction-PY03-04.png](after-prediction-PY03-04.png)（1440×1000）
- [after-tablet.png](after-tablet.png)（768×1024）
- [after-unavailable.png](after-unavailable.png)（1440×1000）
- [after-wrong-comparison.png](after-wrong-comparison.png)（1440×1000）
- [before-drill-desktop.png](before-drill-desktop.png)（1440×1000）
- [before-drill-mobile.png](before-drill-mobile.png)（390×844）
- [before-hints.png](before-hints.png)（1440×1000）
