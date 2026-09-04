# Public prompt inputs / 公开提示词输入

This directory contains the user-created or derived inputs needed to reproduce the two Qwen prompt workflows. It deliberately does **not** contain the four third-party source lexicons, CLP/MELD/E-MELD tables, or Tencent embedding binary. Those materials remain documented in `../external/README.md`.

本目录保存两条 Qwen 提示词流程所需的自建或派生输入，不复制四个第三方原始词表、CLP/MELD/E-MELD 数据表或腾讯词向量二进制文件；这些外部材料见 `../external/README.md`。

| File | Role | Content |
|---|---|---|
| `st_scoring_source_matrix.xlsx` | Actual ST prompt input | The archived 72,820-row source matrix supplied to the semantic-transparency scorer. Columns are `word`, `subtlex`, `yuwei`, `weiruan`, and `xianhan`. It contains source flags, not copies of the source lexicons. |
| `lexical_structure_scoring_input.csv` | Structure prompt input | One `word` column with the same 72,820 words in the published release. The structure classifier sends only this field to Qwen and appends its result columns. |
| `lexical_structure_accuracy_benchmark.xlsx` | Structure evaluation input | The 1,015-item human-curated 12-class benchmark used by `S5_lexical_structure/s2_evaluate_accuracy.py`. Its worksheet names are the reference labels. |

The exact prompt texts used by the public scoring scripts are stored in `../../prompts/`. `s2_score_st.py` and `s1_classify_structure.py` load these files at runtime so the documented prompts cannot silently diverge from the code.

公开脚本实际使用的 prompt 原文见 `../../prompts/`。`s2_score_st.py` 和 `s1_classify_structure.py` 在运行时读取这些文件，避免文档与代码中的提示词悄然不一致。
