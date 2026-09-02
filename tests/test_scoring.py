from __future__ import annotations

import importlib.util
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


scoring = load("scoring", "S1_qwen_scoring/s2_score_st.py")
release = load("release", "S1_qwen_scoring/s3_build_release_dataset.py")
structure = load("structure", "S5_lexical_structure/s1_classify_structure.py")
sources = load("sources", "S1_qwen_scoring/s1_build_source_matrix.py")


class ScoringTests(unittest.TestCase):
    def test_conditional_expectation(self):
        distribution, score = scoring.weighted_score_from_top_logprobs(
            [{"token": " 6", "logprob": math.log(0.25)}, {"token": "7", "logprob": math.log(0.75)}, {"token": "word", "logprob": -0.1}]
        )
        self.assertEqual(distribution, {"6": 0.25, "7": 0.75})
        self.assertEqual(score, 6.75)

    def test_missing_logprobs_fail_closed(self):
        with self.assertRaises(scoring.MissingLogprobsError):
            scoring.weighted_score_from_top_logprobs([{"token": "word", "logprob": 0.0}])

    def test_probability_serialization(self):
        serialized = release.probability_json("1:0.2500, 7:0.7500")
        self.assertEqual(json.loads(serialized), {"1": 0.25, "7": 0.75})

    def test_structure_parser_requires_one_label(self):
        self.assertEqual(structure.parse_structure("偏正"), "偏正")
        with self.assertRaises(ValueError):
            structure.parse_structure("可能是偏正，也可能是联合")

    def test_bigram_filter(self):
        self.assertTrue(sources.is_chinese_bigram("冰箱"))
        self.assertFalse(sources.is_chinese_bigram("阿Q"))
        self.assertFalse(sources.is_chinese_bigram("计算机"))


if __name__ == "__main__":
    unittest.main()

