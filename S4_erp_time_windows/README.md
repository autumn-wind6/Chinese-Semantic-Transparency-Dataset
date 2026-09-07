# S4: ERP Time-Window Analysis and Data Source

## Obtain the Human ERP Data from the Original Article

This stage does not use EEG data collected by this project. It uses the Chinese word-recognition ERP megastudy released by Tsang and Zou as E-MELD. For formal reproduction or public use, obtain the human ERP data through the original article's data-availability statement, supplementary materials, or linked data repository. Do not treat the prepared copy in this repository as the original publication source.

Original article:

> Tsang, Y.-K., & Zou, Y. (2022). An ERP megastudy of Chinese word recognition. *Psychophysiology, 59*(11), e14111. <https://doi.org/10.1111/psyp.14111>

When downloading the data, look for E-MELD, Supporting Information, or the Data Availability Statement in the article. Follow the licensing, citation, and redistribution requirements specified by the article and its data repository.

## Required Files

After downloading and preparing the data according to the original study, place the analysis files at the following locations:

1. `data/input/erp_data_analysis.xlsx`
   - Human ERP data in long format; the current analysis expects 311,202 rows.
   - Required identifier columns: `Subject` and `Item`.
   - Ten dependent-variable time windows: `TW1`-`TW10`, corresponding to 0-100 ms through 900-1000 ms.
   - Control variables: `Dum_HE`, `Dum_AN1`, `Dum_AN2`, `S_W`, `LogCD_W`, `LogCD_C1`, `LogCD_C2`, `LogNOH_C1`, and `LogNOH_C2`.

2. `data/input/erp_item_list.xlsx`
   - Use the `word` worksheet.
   - Required columns: `Item`, `ST_C1_qwen`, and `ST_C2_qwen`.
   - `Item` must match the item identifiers in the ERP long-format data. The script standardizes the two Qwen scores before joining them to the ERP data.

This repository may currently retain prepared copies for organization and verification. Before publishing the repository, check the original data license again to determine whether those copies may be redistributed.

## Analysis

Run:

```bash
Rscript S4_erp_time_windows/s1_erp_time_window_lme.R
```

The script fits a separate linear mixed-effects model to each time window:

```text
TW ~ region and lexical control variables + ST_C1_qwen + ST_C2_qwen + (1|Subject) + (1|Item)
```

It then applies BH-FDR correction separately to the C1 and C2 p-values across the ten time windows and writes:

- `results/erp_time_window_results.xlsx`: coefficients, standard errors, unadjusted p-values, and FDR results for the machine-generated scores in TW1-TW10.
- `results/erp_window_overlap.xlsx`: overlap between time windows significant for the machine-generated scores and those significant for human ratings in the original article.

The reference windows significant for human ratings are taken from Tsang and Zou (2022): TW1, TW7, and TW8 for C1; TW2, TW4, and TW7 for C2. The current script does not re-estimate the human-rating models; it uses the published results as time-window references.
