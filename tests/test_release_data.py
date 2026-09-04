from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/final/chinese_semantic_transparency_lexicon.csv"
DATA_XLSX = ROOT / "data/final/chinese_semantic_transparency_lexicon.xlsx"
INPUTS = ROOT / "data/input"
RESULTS = ROOT / "results"
STRUCTURES = {
    "联合", "偏正", "补充", "动宾", "主谓", "叠音", "重叠", "连绵词", "音译外来词", "前缀", "后缀"
}


class ReleaseDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(DATA)

    def test_shape_and_words(self):
        self.assertEqual(len(self.data), 72820)
        self.assertEqual(self.data["word"].nunique(), 72820)
        self.assertTrue(self.data["word"].str.fullmatch(r"[\u4e00-\u9fff]{2}").all())
        self.assertTrue((self.data["c1"] == self.data["word"].str[0]).all())
        self.assertTrue((self.data["c2"] == self.data["word"].str[1]).all())

    def test_scores_and_qc(self):
        valid = self.data.query("st_qc_status == 'valid'")
        self.assertEqual(len(valid), 72819)
        self.assertTrue(valid["qwen_c1_score"].between(1, 7).all())
        self.assertTrue(valid["qwen_c2_score"].between(1, 7).all())
        missing = self.data.query("st_qc_status != 'valid'")
        self.assertEqual(missing["word"].tolist(), ["乱伦"])
        structure_error = self.data.query("structure_qc_status != 'valid'")
        self.assertEqual(structure_error["word"].tolist(), ["轮奸"])
        self.assertTrue(set(self.data.query("structure_qc_status == 'valid'")["lexical_structure"]).issubset(STRUCTURES))
        for column in ("source_subtlex", "source_yuwei", "source_microsoft", "source_xianhan"):
            self.assertTrue(set(self.data[column]).issubset({0, 1}))

    def test_probability_json(self):
        sample = self.data.query("st_qc_status == 'valid'")
        for column in ("qwen_c1_probability_distribution", "qwen_c2_probability_distribution"):
            for value in sample[column]:
                distribution = json.loads(value)
                self.assertAlmostEqual(sum(distribution.values()), 1.0, places=3)
                self.assertTrue(set(distribution).issubset(set("1234567")))

    def test_csv_xlsx_equivalence(self):
        xlsx = pd.read_excel(DATA_XLSX)
        pd.testing.assert_frame_equal(
            self.data.fillna(""), xlsx.fillna(""), check_dtype=False, check_exact=False, atol=1e-12
        )

    def test_public_prompt_inputs(self):
        source = pd.read_excel(INPUTS / "st_scoring_source_matrix.xlsx")
        self.assertEqual(list(source.columns), ["word", "subtlex", "yuwei", "weiruan", "xianhan"])
        self.assertEqual(source["word"].tolist(), self.data["word"].tolist())
        for old, new in (("subtlex", "source_subtlex"), ("yuwei", "source_yuwei"), ("weiruan", "source_microsoft"), ("xianhan", "source_xianhan")):
            self.assertTrue((source[old].astype(int) == self.data[new].astype(int)).all())

        structure_input = pd.read_csv(INPUTS / "lexical_structure_scoring_input.csv")
        self.assertEqual(list(structure_input.columns), ["word"])
        self.assertEqual(structure_input["word"].tolist(), self.data["word"].tolist())

        benchmark = pd.read_excel(INPUTS / "lexical_structure_accuracy_benchmark.xlsx", sheet_name=None, header=None)
        self.assertEqual(sum(len(sheet) for sheet in benchmark.values()), 1015)

    def test_key_results(self):
        qwen = pd.read_csv(RESULTS / "qwen_human_correlation.csv")
        c1 = qwen.query("position == 'C1' and method == 'Spearman'").iloc[0]
        c2 = qwen.query("position == 'C2' and method == 'Spearman'").iloc[0]
        self.assertEqual(int(c1.n), 8785)
        self.assertAlmostEqual(c1.coefficient, 0.590990, places=6)
        self.assertAlmostEqual(c2.coefficient, 0.538402, places=6)

        baseline = pd.read_csv(RESULTS / "word2vec_human_correlation.csv")
        baseline_c1 = baseline.query("position == 'C1' and method == 'Spearman'").iloc[0]
        baseline_c2 = baseline.query("position == 'C2' and method == 'Spearman'").iloc[0]
        self.assertEqual(int(baseline_c1.n), 8168)
        self.assertAlmostEqual(baseline_c1.coefficient, 0.548657, places=6)
        self.assertAlmostEqual(baseline_c2.coefficient, 0.497271, places=6)

        behavior = pd.read_csv(RESULTS / "behavioral_model_comparison.csv")
        qwen_zrt = behavior.query("outcome == 'zRT' and model == 'qwen_st'").iloc[0]
        self.assertEqual(int(qwen_zrt.n), 8402)
        self.assertAlmostEqual(qwen_zrt.adjusted_r2, 0.422521, places=6)
        audit = pd.read_csv(RESULTS / "behavioral_sample_audit.csv").iloc[0]
        self.assertEqual(int(audit.initial_complete_cases), 8585)
        self.assertEqual(int(audit.excluded_by_zrt_residual), 183)
        self.assertEqual(int(audit.analysis_n), 8402)

        structure = pd.read_csv(RESULTS / "lexical_structure_accuracy.csv")
        overall = structure.query("structure == 'Overall'").iloc[0]
        self.assertEqual(int(overall.n), 1015)
        self.assertEqual(int(overall.correct), 904)
        structure_models = pd.read_csv(RESULTS / "structure_model_comparison.csv")
        self.assertTrue((structure_models["n"] == 8401).all())
        nested = pd.read_csv(RESULTS / "structure_nested_tests.csv")
        zrt_structure = nested.query("outcome == 'zRT' and reduced_model == 'control' and full_model == 'structure'").iloc[0]
        zrt_interaction = nested.query("outcome == 'zRT' and reduced_model == 'main_effects'").iloc[0]
        self.assertAlmostEqual(zrt_structure.F, 8.531146, places=6)
        self.assertAlmostEqual(zrt_interaction.F, 0.698472, places=6)

        erp = pd.read_csv(RESULTS / "erp_time_window_results.csv")
        self.assertEqual(len(erp), 10)
        self.assertTrue(erp["converged"].all())
        self.assertEqual(erp.loc[erp.ST_C1_qwen_sig, "TW"].tolist(), ["TW3", "TW7", "TW8"])
        self.assertEqual(erp.loc[erp.ST_C2_qwen_sig, "TW"].tolist(), [])

        correlation_summary = pd.read_csv(RESULTS / "correlation_summary.csv")
        self.assertEqual(len(correlation_summary), 12)
        self.assertEqual(set(correlation_summary["analysis"]), {"qwen_vs_human", "word2vec_vs_human", "human_split_half"})


if __name__ == "__main__":
    unittest.main()
