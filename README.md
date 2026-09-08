# Chinese Semantic Transparency and Lexical Structure

This repository was organized from the final research outputs and follows the actual study sequence: semantic-transparency scoring, correlation validation, incremental behavioral variance, ERP time-window analysis, and lexical-structure analysis. All scripts read their default inputs from the repository's `data/` directory and write outputs to `data/final/` or `results/`; no paths need to be edited in the scripts.

## 1. Data Scope

- `data/input/LDT.xlsx` contains 20,044 rows. Retaining real words with non-missing `C1.ST` values produces a scoring set of 8,785 words.
- `data/final/Qwen_ST.xlsx` is the archived Qwen scoring output for those 8,785 words and is the data source for the correlation and behavioral analyses.
- `data/input/st_scoring_source_matrix.xlsx` contains 65,892 two-character candidate words produced by merging and filtering the SUBTLEX, yuwei, and xianhan lexicons. Words found in SUBTLEX also retain the original `WCount` frequency value.
- `data/final/chinese_semantic_transparency_lexicon.xlsx` is the expanded 65,892-row lexicon. It includes C1/C2 semantic-transparency scores, SUBTLEX frequencies, and lexical-structure labels. See [`data/final/README.md`](data/final/README.md) for details.

## 2. Repository Structure

```text
data/
├── external/                    SUBTLEX, xianhan, and yuwei lexicons
├── input/                       Inputs for scoring and statistical analyses
└── final/                       Results for 8,785 words and the 65,892-row expanded lexicon
S1_qwen_scoring/                 Source-matrix construction and Qwen semantic-transparency scoring
S2_correlation_validation/       Qwen/Word2Vec-to-human correlations and human-rating split-half analysis
S3_behavioral_variance/          Incremental variance in zRT and ERR
S4_erp_time_windows/             Ten ERP time windows
S5_lexical_structure/            Lexical-structure scoring and incremental-variance analysis
results/                         Final numerical results
```

## 3. API Configuration

Copy the configuration template and enter the API endpoint and key only in your local `.env` file:

```bash
cp .env.example .env
```

```dotenv
QWEN_API_KEY=your_api_key
QWEN_BASE_URL=your_api_endpoint
QWEN_MODEL=qwen3-max

# Leave QWEN_STRUCTURE_API_KEY empty if lexical-structure scoring uses the same key.
QWEN_STRUCTURE_API_KEY=
QWEN_STRUCTURE_BASE_URL=your_api_endpoint
QWEN_STRUCTURE_MODEL=qwen3.5-397b-a17b

# Absolute local path to the Tencent Chinese Word2Vec file stored outside this repository.
TENCENT_W2V_BIN=/path/to/light_Tencent_AILab_ChineseEmbedding.bin
```

`.env` is excluded by `.gitignore`, so real credentials will not be committed. System environment variables can also override values in `.env`.

## 4. Inputs, Scripts, and Outputs by Stage

### S1: Semantic-Transparency Scoring

| Order | Script | Default input | Default output | Description |
|---|---|---|---|---|
| 1 | `S1_qwen_scoring/s1_build_scoring_input.py` | Three lexicons in `data/external/` | `data/input/st_scoring_source_matrix.xlsx` | Merges, deduplicates, and filters two-character words; does not call an API |
| 2 | `S1_qwen_scoring/s2_score_semantic_transparency.py` | `data/input/LDT.xlsx` | `data/final/Qwen_ST_rerun.xlsx` | Scores 8,785 real words; calls a paid API |

To score the 8,785-word set directly:

```bash
python S1_qwen_scoring/s2_score_semantic_transparency.py
```

By default, the script writes to the new filename `Qwen_ST_rerun.xlsx` and does not overwrite the archived `Qwen_ST.xlsx`. To rebuild and rescore the 65,892-word input:

```bash
python S1_qwen_scoring/s1_build_scoring_input.py
python S1_qwen_scoring/s2_score_semantic_transparency.py \
  --input data/input/st_scoring_source_matrix.xlsx \
  --word-column word \
  --filter-column "" \
  --real-column "" \
  --output data/final/expanded_st_scores_rerun.xlsx
```

### S2: Correlation Validation

| Order | Script | Default input | Default output |
|---|---|---|---|
| 1 | `S2_correlation_validation/s1_qwen_human_correlation.py` | `data/final/Qwen_ST.xlsx` | `results/qwen_human_correlation.xlsx` |
| 2 | `S2_correlation_validation/s2_word2vec_baseline.py` | `data/final/Qwen_ST.xlsx` and the external Tencent word vectors | `results/word2vec_human_correlation.xlsx` |
| 3 | `S2_correlation_validation/s3_rater_split_half.py` | `data/input/human_rating_validation.xlsx` | `results/human_split_half_correlation.xlsx` |

```bash
python S2_correlation_validation/s1_qwen_human_correlation.py
python S2_correlation_validation/s2_word2vec_baseline.py \
  --embedding-binary /path/to/light_Tencent_AILab_ChineseEmbedding.bin
python S2_correlation_validation/s3_rater_split_half.py
```

These three scripts compute and export numerical results only; they do not generate figures. The Tencent word-vector file is too large to include in the repository. Its absolute path can instead be configured with `TENCENT_W2V_BIN` in `.env`. If the input already contains `cos_C1_Word` and `cos_C2_Word`, use `--reuse-cosines` to avoid loading the word vectors again.

### S3: Incremental Behavioral Variance

| Script | Default input | Default output |
|---|---|---|
| `S3_behavioral_variance/s1_behavioral_incremental_variance.R` | `data/input/behavioral_variance_input.xlsx` | `results/behavioral_model_comparison.xlsx` and `results/behavioral_sample_audit.xlsx` |

```bash
Rscript S3_behavioral_variance/s1_behavioral_incremental_variance.R
```

This script reproduces the baseline, human-ST, Qwen-ST, and combined model comparisons for zRT and ERR.

### S4: ERP Time Windows

The human ERP data come from the E-MELD dataset by Tsang and Zou (2022). They must be obtained through the data-availability statement or supplementary materials of the [original article](https://doi.org/10.1111/psyp.14111). Download instructions, field preparation, and citation requirements are documented in [`S4_erp_time_windows/README.md`](S4_erp_time_windows/README.md).

| Script | Default input | Default output |
|---|---|---|
| `S4_erp_time_windows/s1_erp_time_window_lme.R` | `data/input/erp_item_list.xlsx` and `data/input/erp_data_analysis.xlsx` | `results/erp_time_window_results.xlsx` and `results/erp_window_overlap.xlsx` |

```bash
Rscript S4_erp_time_windows/s1_erp_time_window_lme.R
```

The script fits mixed-effects models for TW1-TW10 and applies BH-FDR correction separately to the C1 and C2 p-values.

### S5: Lexical Structure

| Order | Script | Default input | Default output | Description |
|---|---|---|---|---|
| 1 | `S5_lexical_structure/s1_classify_structure.py` | `data/input/lexical_structure_scoring_input.xlsx` | `data/final/lexical_structure_scores.xlsx` | Assigns one of 11 lexical-structure classes to 65,892 words; calls a paid API |
| 2 | `S5_lexical_structure/s2_structure_incremental_variance.R` | `data/input/behavioral_variance_input.xlsx` and `data/final/chinese_semantic_transparency_lexicon.xlsx` | `results/structure_model_comparison.xlsx` and `results/structure_nested_tests.xlsx` | Tests incremental lexical-structure variance and ST-by-structure interactions |

The held-out gold standard for testing 11-class lexical-structure models is `data/input/lexical_structure_gold_1000.xlsx` (1,001 words). Each sheet name is the gold structure label; column 1 is the word and column 2 is an existing model prediction. Complement is kept as a single class. This file is for model evaluation and is not a default input of the S5 scripts.

```bash
python S5_lexical_structure/s1_classify_structure.py
Rscript S5_lexical_structure/s2_structure_incremental_variance.R
```

## 5. Dependencies and Execution Order

Python 3.10+ and R 4.3+ are recommended:

```bash
python -m pip install -r requirements.txt
Rscript requirements.R
```

To reproduce the existing analysis results, run S2, S3, S4, and the S5 variance script in that order. Qwen does not need to be called again. Run the S1 scoring script or the S5 classification script only when regenerating scores or labels.

## 6. Scope and Exclusions

The Word2Vec baseline script retains the Tencent-vector cosine-similarity calculations and their correlations with human ratings; the large binary word-vector file remains an external dependency. The held-out gold standard for testing 11-class lexical-structure models is `data/input/lexical_structure_gold_1000.xlsx` (1,001 words; sheet name is the gold label). This repository does not include plotting code, figures, exploratory notebooks, or experimental materials from other working directories.
