# Final Data Files

## `chinese_semantic_transparency_lexicon.csv`

This file is the expanded semantic-transparency lexicon of Chinese two-character words prepared for this repository. It is UTF-8 encoded, contains 65,892 rows, and has no duplicate values in `word`.

Candidate words were merged, filtered, and deduplicated from three sources:

- SUBTLEX-CH-WF
- The yuwei word list
- An export of the *Modern Chinese Dictionary* (xianhan)

## Fields

| Field | Type | Description |
|---|---|---|
| `word` | String | Unique two-character candidate word |
| `c1` | String | First character or morpheme |
| `c2` | String | Second character or morpheme |
| `source_subtlex` | 0/1 integer | Whether the word occurs in SUBTLEX-CH-WF |
| `source_yuwei` | 0/1 integer | Whether the word occurs in the yuwei word list |
| `source_xianhan` | 0/1 integer | Whether the word occurs in the *Modern Chinese Dictionary* export |
| `subtlex_wcount` | Nullable integer | Original `WCount` frequency from SUBTLEX-CH-WF; missing when the word is absent from SUBTLEX |
| `qwen_c1_probability_distribution` | JSON string | Renormalized distribution over valid ratings from 1 to 7 among the top-five candidates for the first C1 token |
| `qwen_c1_score` | Float | Probability-weighted C1 semantic-transparency score in the range 1-7 |
| `qwen_c2_probability_distribution` | JSON string | Renormalized distribution over valid ratings from 1 to 7 among the top-five candidates for the first C2 token |
| `qwen_c2_score` | Float | Probability-weighted C2 semantic-transparency score in the range 1-7 |
| `lexical_structure` | String | One of the 11 lexical-structure labels assigned by Qwen |

The 11 lexical-structure classes are coordinate, modifier-head, complement, verb-object, subject-predicate, reduplicative-sound, full reduplication, inseparable disyllabic, phonetic loanword, prefix-derived, and suffix-derived.

## Data Integrity

| Check | Result |
|---|---:|
| Total rows | 65,892 |
| Unique words | 65,892 |
| Included in SUBTLEX | 45,871 |
| Included in yuwei | 39,961 |
| Included in xianhan | 41,469 |
| Rows with SUBTLEX `WCount` | 45,871 |
| Rows absent from SUBTLEX with frequency left blank | 20,021 |

`source_subtlex=1` corresponds exactly to a non-missing `subtlex_wcount`. A blank frequency means that the word is absent from SUBTLEX; it must not be interpreted as an observed frequency of zero.

Two scoring records are currently incomplete:

- The word with Unicode code points `U+4E71 U+4F26` lacks C1/C2 Qwen probability distributions and scores but has a lexical-structure label.
- The word with Unicode code points `U+8F6E U+5978` has C1/C2 Qwen scores but lacks a lexical-structure label.

All other records have complete semantic-transparency scores and lexical-structure labels.

## Scoring and Source Scripts

- Three-lexicon input construction and SUBTLEX frequencies: [`s1_build_scoring_input.py`](../../S1_qwen_scoring/s1_build_scoring_input.py)
- C1/C2 Qwen semantic-transparency scoring: [`s2_score_semantic_transparency.py`](../../S1_qwen_scoring/s2_score_semantic_transparency.py)
- Eleven-class lexical-structure scoring: [`s1_classify_structure.py`](../../S5_lexical_structure/s1_classify_structure.py)

The probability-distribution fields contain JSON text within the CSV. With pandas, parse them as follows:

```python
import json
import pandas as pd

lexicon = pd.read_csv("data/final/chinese_semantic_transparency_lexicon.csv")
c1_distribution = json.loads(lexicon.loc[0, "qwen_c1_probability_distribution"])
```

Complete field definitions are also available in the parent directory's [`data_dictionary.csv`](../data_dictionary.csv). Licensing, citation, and redistribution terms for the three external lexicons are governed by their original publication sources.

## `Qwen_ST.xlsx`

This file archives Qwen scores for 8,785 real experimental words. It is used for the Qwen-to-human correlation, Word2Vec baseline, and behavioral-variance analyses. Its purpose differs from that of the 65,892-row expanded lexicon described above.
