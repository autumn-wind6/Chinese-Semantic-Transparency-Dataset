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

Known public references include Cai and Brysbaert (2010) for SUBTLEX-CH, Tsang et al. (2018) for MELD-SCH, Tse et al. (2017) for CLP, Tsang and Zou (2022) for E-MELD, and Song et al. (2018) for the Tencent embeddings. Exact download URLs and the three pending source identities must be confirmed before public release.

