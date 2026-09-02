#!/usr/bin/env python3
"""Independent Python audit of the canonical R OLS analyses.

This utility requires the non-distributed external analysis tables. It exists
to verify archived numeric results on machines where R is unavailable; the R
scripts remain the canonical public analysis entry points.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm


CONTROLS_ALL = [
    "LogWF", "Stroke", "C1.LogCF", "C2.LogCF", "C1.LogFS.Type", "C2.LogFS.Type",
    "C1.LogNoM", "C2.LogNoM", "C1.LogNoP", "C2.LogNoP",
]
CONTROLS = [
    "LogWF", "Stroke", "C1.LogCF", "C2.LogCF", "C1.LogFS.Type", "C2.LogFS.Type",
    "C2.LogNoM", "C1.LogNoP",
]
METRICS = ["C1.ST", "C2.ST", "C1.ST_qwen", "C2.ST_qwen", "human_average", "qwen_average"]
STRUCTURES = ["联合", "偏正", "补充", "动宾", "主谓", "叠音", "重叠", "连绵词", "音译外来词", "前缀", "后缀"]


def fit(data: pd.DataFrame, outcome: str, columns: list[str]) -> sm.regression.linear_model.RegressionResultsWrapper:
    design = sm.add_constant(data[columns].astype(float), has_constant="add")
    return sm.OLS(data[outcome].astype(float), design).fit()


def prepare_behavior(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    data = pd.read_csv(path)
    required = ["Word", "C1", "C2", "Real", "zRT", "ERR", *CONTROLS_ALL, *METRICS]
    data = data.loc[(data["ERR"] <= 30) & (data["Real"] == 1), required].dropna().copy()
    for column in [*CONTROLS_ALL, *METRICS]:
        data[column] = pd.to_numeric(data[column], errors="raise") - pd.to_numeric(data[column], errors="raise").mean()
    initial = fit(data, "zRT", CONTROLS_ALL)
    residual_z = (initial.resid - initial.resid.mean()) / initial.resid.std(ddof=1)
    kept = data.loc[residual_z.abs() < 2.5].copy()
    return kept, {"initial_complete_cases": len(data), "excluded_by_zrt_residual": int((residual_z.abs() >= 2.5).sum()), "analysis_n": len(kept)}


def behavioral_results(data: pd.DataFrame) -> pd.DataFrame:
    specs = {
        "baseline": CONTROLS,
        "human_st": [*CONTROLS, "C1.ST", "C2.ST"],
        "qwen_st": [*CONTROLS, "C1.ST_qwen", "C2.ST_qwen"],
        "human_and_qwen_st": [*CONTROLS, "C1.ST", "C2.ST", "C1.ST_qwen", "C2.ST_qwen"],
    }
    rows = []
    for outcome in ("zRT", "ERR"):
        fits = {name: fit(data, outcome, cols) for name, cols in specs.items()}
        baseline = fits["baseline"]
        for name, model in fits.items():
            if name == "baseline":
                nested_f = nested_p = nested_df = np.nan
            else:
                nested_f, nested_p, nested_df = model.compare_f_test(baseline)
            rows.append(
                {
                    "outcome": outcome, "model": name, "n": int(model.nobs),
                    "r2": model.rsquared, "adjusted_r2": model.rsquared_adj,
                    "delta_r2": model.rsquared - baseline.rsquared,
                    "delta_adjusted_r2": model.rsquared_adj - baseline.rsquared_adj,
                    # R's lm logLik counts residual scale as one extra parameter.
                    "AIC": model.aic + 2, "BIC": model.bic + np.log(model.nobs), "nested_df": nested_df,
                    "nested_F": nested_f, "nested_p": nested_p,
                }
            )
    return pd.DataFrame(rows)


def structure_results(data: pd.DataFrame, structure_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    structure = pd.read_csv(structure_path)
    word_col = "Word" if "Word" in structure else "word"
    label_col = "词汇结构" if "词汇结构" in structure else "lexical_structure"
    if {"C1_ST_qwen", "C2_ST_qwen"}.issubset(structure):
        c1_col, c2_col = "C1_ST_qwen", "C2_ST_qwen"
    elif {"C1_ST", "C2_ST"}.issubset(structure):
        c1_col, c2_col = "C1_ST", "C2_ST"
    else:
        c1_col, c2_col = "qwen_c1_score", "qwen_c2_score"
    structure = structure.loc[
        structure[label_col].isin(STRUCTURES), [word_col, label_col, c1_col, c2_col]
    ].copy()
    structure.columns = ["Word", "词汇结构", "Qwen_C1", "Qwen_C2"]
    structure["SemTrans_Mean"] = structure[["Qwen_C1", "Qwen_C2"]].mean(axis=1)
    merged = data.merge(structure, on="Word", how="inner").dropna().copy()
    merged["SemTrans_Mean_c"] = merged["SemTrans_Mean"] - merged["SemTrans_Mean"].mean()
    dummies = pd.get_dummies(merged["词汇结构"], prefix="structure", dtype=float)
    reference = "structure_偏正"
    dummies = dummies.drop(columns=[reference])
    for column in dummies:
        merged[column] = dummies[column]
        merged[f"interaction_{column}"] = dummies[column] * merged["SemTrans_Mean_c"]
    dummy_cols = list(dummies)
    interaction_cols = [f"interaction_{column}" for column in dummy_cols]
    specs = {
        "control": CONTROLS,
        "structure": [*CONTROLS, *dummy_cols],
        "main_effects": [*CONTROLS, "SemTrans_Mean_c", *dummy_cols],
        "interaction": [*CONTROLS, "SemTrans_Mean_c", *dummy_cols, *interaction_cols],
    }
    summary_rows, comparison_rows = [], []
    for outcome in ("zRT", "ERR"):
        fits = {name: fit(merged, outcome, columns) for name, columns in specs.items()}
        for name, model in fits.items():
            summary_rows.append(
                {"outcome": outcome, "model": name, "n": int(model.nobs), "r2": model.rsquared, "adjusted_r2": model.rsquared_adj, "AIC": model.aic + 2, "BIC": model.bic + np.log(model.nobs)}
            )
        for reduced, full in (("control", "structure"), ("control", "main_effects"), ("main_effects", "interaction")):
            f_value, p_value, df = fits[full].compare_f_test(fits[reduced])
            comparison_rows.append({"outcome": outcome, "reduced_model": reduced, "full_model": full, "df": df, "F": f_value, "p_value": p_value})
    return pd.DataFrame(summary_rows), pd.DataFrame(comparison_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--behavior", type=Path, required=True, help="CSV equivalent of the external intersection table")
    parser.add_argument("--structure", type=Path, required=True, help="CSV equivalent of the scored validation table")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    behavior, audit = prepare_behavior(args.behavior)
    behavioral_results(behavior).to_csv(args.output_dir / "behavioral_model_comparison.csv", index=False)
    pd.DataFrame([audit]).to_csv(args.output_dir / "behavioral_sample_audit.csv", index=False)
    models, tests = structure_results(behavior, args.structure)
    models.to_csv(args.output_dir / "structure_model_comparison.csv", index=False)
    tests.to_csv(args.output_dir / "structure_nested_tests.csv", index=False)
    print(pd.DataFrame([audit]).to_string(index=False))
    print(behavioral_results(behavior).to_string(index=False))
    print(models.to_string(index=False))
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
