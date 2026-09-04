# External data / 外部数据

This directory is intentionally empty in version control. The analyses use third-party datasets and models that must be obtained from their original providers. Do not commit them here.

本目录在 Git 中有意保持为空。分析依赖第三方数据集和模型，需从原始提供方取得，请勿将原文件提交到本仓库。

## Expected inputs / 预期输入

| Analysis | Local input | Required content |
|---|---|---|
| S1 source aggregation | SUBTLEX-CH-WF plus the local `yuwei`, Microsoft-format and Modern Chinese Dictionary lists | Source word lists; the last three formal citations are pending author confirmation |
| S2 human validation | SemTransCNC 1.0 / CLP-derived item table | `Word`, human `C1.ST`/`C2.ST`, Qwen score columns |
| S2 embedding baseline | Tencent AI Lab Chinese Embedding binary | Word2Vec-format binary; Song et al. (2018) |
| S3 behavioral validity | MELD-SCH/CLP merged item table | `zRT`, `ERR`, `Real`, lexical controls and human/Qwen ST |
| S4 ERP validity | E-MELD item list and long analysis table | `Item`, Qwen ST, `Subject`, TW1–TW10 and the published controls |

## Local staging names / 本地暂存文件名

The following four S1 source files are currently staged locally in this directory and are ignored by Git. They are available for local reproduction only and will not be included in a public commit.

以下四份 S1 来源文件已暂存在本目录，并被 Git 忽略；它们仅供本地复现，不会进入公开提交。

| Local filename | Original role | Script argument |
|---|---|---|
| `SUBTLEX-CH-WF.xlsx` | SUBTLEX-CH word-frequency source | `--subtlex` |
| `yuwei.txt` | Local yuwei word list | `--yuwei` |
| `weiruan.src` | Local Microsoft-format lexicon | `--microsoft` |
| `xianhan.doc` | Local Modern Chinese Dictionary export | Convert to UTF-8 plain text first, then pass the text file to `--xianhan-text` |

`s1_build_source_matrix.py` deliberately reads a UTF-8 text export for the final item because legacy `.doc` parsing is not cross-platform. The `.doc` file is retained locally as the source artifact; its converted text derivative should also remain untracked.

Known public references include Cai and Brysbaert (2010) for SUBTLEX-CH, Tsang et al. (2018) for MELD-SCH, Tse et al. (2017) for CLP, Tsang and Zou (2022) for E-MELD, and Song et al. (2018) for the Tencent embeddings. Exact download URLs and the three pending source identities must be confirmed before public release.
