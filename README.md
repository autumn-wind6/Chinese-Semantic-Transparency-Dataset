# ST: Chinese Semantic Transparency Norms and Validation

> 中文说明见下方“中文概览”。Repository name `ST` is temporary and can be changed before publication.

This repository contains the release dataset, reproducible code, and compact results for large-scale Qwen semantic-transparency scoring of Chinese two-character candidate words. The organization follows the research workflow: scoring, convergent validity, behavioral incremental variance, ERP time-window validity, and lexical-structure analysis.

The original working directory is not part of this repository. Early GPT/Grok/DeepSeek experiments, failed fine-tuning attempts, manuscripts, literature PDFs, presentation files, and exploratory duplicates are intentionally excluded.

## Repository structure

```text
S1_qwen_scoring/             source aggregation and qwen3-max ST scoring
S2_correlation_validation/   human and static-embedding correlations
S3_behavioral_variance/      zRT/ERR incremental explained variance
S4_erp_time_windows/         E-MELD mixed-effects time-window analysis
S5_lexical_structure/        Qwen3.5 structure labels, accuracy, and variance
data/final/                  72,820-row public release in CSV and XLSX
data/input/                  public Qwen prompt inputs and structure benchmark
data/external/               instructions only; third-party data are excluded
prompts/                     archived prompt texts loaded by the scoring scripts
results/                     machine-readable result tables
figures/                     reproducible summary figures
tests/                       offline tests and independent numeric audit
```

## Main dataset

The canonical file is `data/final/chinese_semantic_transparency_lexicon.csv`; an equivalent Excel version is provided. It contains 72,820 unique two-character candidates and the stable fields documented in `data/data_dictionary.csv`.

- 72,818 rows have valid ST scores and lexical-structure labels.
- `乱伦` is retained with `st_qc_status=missing_score` because no usable C1/C2 score was archived.
- `轮奸` is retained with `structure_qc_status=api_error`; its ST scores remain valid.
- A source string passing the two-character filter is a candidate lexical item, not a claim that it is an independently verified modern-Chinese dictionary word.

Probability fields are JSON objects. They contain legal rating tokens found among the first token's top-5 log probabilities, renormalized to sum to one. The score is their conditional expectation on the 1–7 scale; it is not a calibrated full seven-class probability distribution.

## Public prompt inputs

`data/input/` contains the archived 72,820-word source matrix actually passed into ST scoring, a word-only input for the 11-class lexical-structure classifier, and the 1,015-item human-curated structure benchmark. The exact historical prompts are stored in `prompts/` and are loaded directly by the two Qwen scripts. See `data/input/README.md` for bilingual provenance and scope notes.

`data/input/` 保存实际传入 ST 评分的 72,820 词来源矩阵、11 类词汇结构分类所需的逐词输入，以及 1,015 项人工结构评估集。历史 prompt 原文保存在 `prompts/`，并由两份 Qwen 脚本直接读取；中英文来源与范围说明见 `data/input/README.md`。

```python
import json
import pandas as pd

norms = pd.read_csv("data/final/chinese_semantic_transparency_lexicon.csv")
usable = norms.query("st_qc_status == 'valid' and structure_qc_status == 'valid'")
distribution = json.loads(usable.iloc[0].qwen_c1_probability_distribution)
```

## Models and analysis order

1. **Qwen scoring.** ST was generated with `qwen3-max`, temperature 0, first-token logprobs, and top-logprobs 5. `s2_score_st.py` fails closed if an endpoint omits logprobs and supports checkpoints/resume. Existing release scores are not re-requested.
2. **Convergent validity.** Qwen scores are compared with human ratings; Tencent static Chinese embeddings provide a geometric baseline. Human-rating split-half correlations validate the archived mean columns.
3. **Behavioral validity.** OLS models predict MELD-SCH item-level zRT and ERR after retaining real words, applying ERR ≤ 30, complete-case filtering, centering continuous predictors, and excluding observations with absolute z-scored residuals ≥ 2.5 from the initial zRT control model. The common analysis sample is 8,402 items.
4. **ERP validity.** Ten E-MELD 100-ms windows are modeled with Qwen C1/C2, published lexical/region controls, and random intercepts for subject and item. C1 and C2 p-values are BH-FDR corrected separately.
5. **Lexical structure.** Production labels use Qwen3.5-397B-A17B and an 11-class taxonomy. The human benchmark retains 12 classes by separating 补充v and 补充n. Structure analyses use 8,401 behavioral items.

Model metadata are stored in `data/model_metadata.json`.

## Key results

- Qwen–human Spearman correlations: C1 ρ=.5910 and C2 ρ=.5384 (N=8,785).
- Static-embedding Spearman correlations: C1 ρ=.5487 and C2 ρ=.4973 (common N=8,168).
- Qwen ST significantly improves zRT and ERR models beyond lexical controls; its adjusted-R² increases are .0032 and .0040, respectively.
- Qwen C1 is FDR-significant at TW3, TW7, and TW8. The human/Qwen C1 overlap is TW7–TW8 (600–800 ms); Qwen C2 has no FDR-significant window.
- The 12-class structure benchmark accuracy is 89.06% (904/1,015).
- Production structure labels add significant zRT and ERR variance; ST-by-structure interactions are not significant.

Full-precision values are in `results/` and summarized in `results/KEY_FINDINGS.md`.

## Reproduction

Python 3.10+ and R 4.3+ are recommended.

```bash
python -m pip install -r requirements.txt
Rscript requirements.R
python -m unittest discover -s tests -p 'test_*.py' -v
```

Each numbered script accepts explicit input/output arguments and uses no machine-specific absolute paths. See `data/external/README.md` for third-party inputs. Paid API scripts are never invoked by the test suite.

Representative commands:

```bash
python S2_correlation_validation/s1_qwen_human_correlation.py --help
python S2_correlation_validation/s4_build_correlation_summary.py --help
Rscript S3_behavioral_variance/s1_behavioral_incremental_variance.R INPUT.xlsx results
Rscript S4_erp_time_windows/s1_erp_time_window_lme.R ITEM_LIST.xlsx DATA.csv results
Rscript S5_lexical_structure/s3_structure_incremental_variance.R BEHAVIOR.xlsx data/final/chinese_semantic_transparency_lexicon.xlsx results
```

The following commands use the public prompt inputs but make paid API requests, so they are examples for a future rerun rather than release-building commands:

```bash
python S1_qwen_scoring/s2_score_st.py \
  --input data/input/st_scoring_source_matrix.xlsx \
  --output OUTPUT.xlsx
python S5_lexical_structure/s1_classify_structure.py \
  --input data/input/lexical_structure_scoring_input.csv \
  --output OUTPUT.csv
python S5_lexical_structure/s2_evaluate_accuracy.py \
  --input data/input/lexical_structure_accuracy_benchmark.xlsx \
  --output results/lexical_structure_accuracy.csv \
  --errors results/lexical_structure_errors.csv
```

## Data, provenance, and release status

Third-party raw datasets and embedding binaries are not redistributed. Formal names, versions, and URLs for the local `yuwei`, Microsoft-format, and Modern Chinese Dictionary source lists still require author confirmation. Until those entries are completed, this repository is locally Git-ready but not cleared for a public remote.

No license is granted at this stage. All rights are reserved until the authors confirm code and derived-data licensing.

## 中文概览

本仓库整理了汉语双字词语义透明度的最终公开版数据、分析代码和结果。研究流程分为五步：Qwen 概率评分、与人工评分及静态词向量的相关验证、对词汇判断行为的方差增量、ERP 时间窗一致性、词汇结构分类及其附加解释量。

最终主表保留 72,820 个唯一双字候选词，并同时提供 CSV 与 Excel。字段采用稳定英文命名，完整中英文解释见 `data/data_dictionary.csv`。第三方原始数据、词向量和未确认授权的原始词表不上传；仓库只提供来源与放置说明。当前无许可证，在三项词表正式出处和授权口径补齐前不应建立公开 GitHub 远程仓库。

## References / 主要参考文献

- Cai, Q., & Brysbaert, M. (2010). SUBTLEX-CH: Chinese word and character frequencies based on film subtitles. *PLoS ONE, 5*(6), e10729.
- Song, Y., Shi, S., Li, J., & Zhang, H. (2018). Directional skip-gram: Explicitly distinguishing left and right context for word embeddings. *NAACL-HLT*.
- Tsang, Y.-K., Huang, J., Lui, M., Xue, M., Chan, Y.-W. F., Wang, S., & Chen, H.-C. (2018). MELD-SCH: A megastudy of lexical decision in simplified Chinese. *Behavior Research Methods, 50*, 1763–1777.
- Tsang, Y.-K., & Zou, Y. (2022). An ERP megastudy of Chinese word recognition. *Psychophysiology, 59*(11), e14111.
- Tse, C.-S., Yap, M. J., Chan, Y.-L., Sze, W. P., Shaoul, C., & Lin, D. (2017). The Chinese Lexicon Project. *Behavior Research Methods, 49*, 1079–1098.
- Wang, X., & Xu, X. (2025). Composition as nonlinear combination in semantic space: A computational characterization of Chinese compound words. *Cognitive Science*.
