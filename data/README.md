# Data Map

All retained scripts read their default inputs from this directory and do not depend on absolute paths from the original working directory. The human ERP data were originally released as part of the E-MELD dataset by Tsang and Zou (2022). For a formal reproduction, obtain the data from the original article and comply with its data license. See [`S4_erp_time_windows/README.md`](../S4_erp_time_windows/README.md) for details.

`S1_qwen_scoring/s1_build_scoring_input.py` can regenerate `input/st_scoring_source_matrix.xlsx` from the three lexicons in `external/`. On macOS, the script uses the built-in `textutil` utility to read `xianhan.doc`. On other systems, install `antiword` or pass a UTF-8 text export with `--xianhan`.

| File | Rows | Purpose | Source in the original research outputs |
|---|---:|---|---|
| `external/SUBTLEX-CH-WF.xlsx` | - | SUBTLEX-CH lexicon | SUBTLEX-CH-WF workbook in the lexical-expansion materials |
| `external/xianhan.doc` | - | Export of the *Modern Chinese Dictionary* | `xianhan.doc` in the lexical-expansion materials |
| `external/yuwei.txt` | - | yuwei word list | `yuwei.txt` in the lexical-expansion materials |
| `input/LDT.xlsx` | 20,044 | Raw semantic-transparency scoring input; filtering for real words with non-missing `C1.ST` leaves 8,785 words | `LDT.xlsx` in the original Qwen-scoring materials |
| `input/st_scoring_source_matrix.xlsx` | 65,892 | Expanded scoring input from three lexicons | Regenerated from the three sources included in this repository |
| `input/lexical_structure_scoring_input.xlsx` | 65,892 | Lexical-structure scoring input | Extracted from the `word` column of the final expanded output |
| `input/lexical_structure_gold_1000.xlsx` | 1,001 | Held-out gold standard for testing 11-class lexical-structure models (sheet name = gold label; column 1 = word; column 2 = existing model output). Complement is a single class (`补充` / COMP), not split into n/v | Original working file `structure_0330 DSC.xlsx` |
| `input/human_rating_validation.xlsx` | 1,176 | Human-rating mean validation and split-half analysis | Merged crowdsourced semantic-transparency dataset |
| `input/behavioral_variance_input.xlsx` | 8,785 | zRT/ERR and lexical-structure variance analyses | Intersection dataset from the original Qwen-scoring materials |
| `input/erp_item_list.xlsx` | 1,020 real words | ERP items and machine-generated ST scores | `item_list.xlsx` from the original data-analysis materials |
| `input/erp_data_analysis.xlsx` | 311,202 | ERP data in long format | `data_analysis.csv` from the original data-analysis materials |
| `final/Qwen_ST.xlsx` | 8,785 | Archived Qwen scores for the 8,785-word set | `Qwen_ST.xlsx` from the original Qwen-scoring materials |
| `lexical_structure_labels.xlsx` | 11 | Chinese-to-English lexical-structure codebook | `structure label(1).xlsx`, with complement unified as COMP |
| `final/chinese_semantic_transparency_lexicon.xlsx` | 65,892 | Final expanded lexicon | Normalized export after removing words unique to one excluded source |

For fields, provenance, and integrity checks for the final expanded lexicon, see [`final/README.md`](final/README.md). Consolidated field definitions are available in [`data_dictionary.xlsx`](data_dictionary.xlsx).
