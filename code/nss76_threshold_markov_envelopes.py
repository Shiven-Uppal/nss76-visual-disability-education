#!/usr/bin/env python3
"""Propagate explicit school-participation thresholds through NSS-identified sets.

The input effect is a counterfactual increment in participation at ages 3--5.
It is not estimated from NSS.  Every endpoint combination of the sharp
age-stage transition sets is evaluated, giving a structural uncertainty
envelope for later occupancies.
"""
from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

AGES = ["3-5", "6-10", "11-14", "15-17"]


def matrix(entry: float, exit_: float) -> np.ndarray:
    """Rows: not enrolled/enrolled; columns: next not/enrolled."""
    return np.array([[1.0 - entry, entry], [exit_, 1.0 - exit_]])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transition-sets", type=Path, required=True)
    ap.add_argument("--targets", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--effects",
        default="0,0.05,0.10,0.20",
        help="Comma-separated assumed increments in age-3--5 participation.",
    )
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    transitions = pd.read_csv(args.transition_sets)
    trans = transitions.loc[transitions.state.eq("ordinary_school_current")].copy()
    trans["order"] = trans.from_age_stage.map({a: i for i, a in enumerate(AGES)})
    trans = trans.sort_values("order")
    if list(trans.from_age_stage) != AGES[:-1]:
        raise ValueError("School transition stages are incomplete or out of order.")

    target = pd.read_csv(args.targets)
    baseline = (
        target.loc[target.target.eq("ordinary_school_current")]
        .set_index("age_band")
        .loc[AGES, "weighted_probability"]
        .astype(float)
    )
    m0 = float(baseline.iloc[0])
    effects = [float(x) for x in args.effects.split(",")]
    if any(x < 0 or x > 1 - m0 for x in effects):
        raise ValueError(f"Effects must lie in [0, {1-m0:.8f}].")

    endpoint_matrices = []
    for row in trans.itertuples(index=False):
        endpoint_matrices.append(
            [
                ("lower_entry", matrix(row.entry_lower, row.exit_lower)),
                ("upper_entry", matrix(row.entry_upper, row.exit_upper)),
            ]
        )

    rows = []
    # The four school-age stages give only 2^3 = 8 sharp-set endpoint paths.
    for delta in effects:
        baseline_state = np.array([1.0 - m0, m0])
        policy_state = np.array([1.0 - (m0 + delta), m0 + delta])
        by_stage = {age: [] for age in AGES}
        by_stage[AGES[0]].append((policy_state[1], "initial"))
        for choices in product([0, 1], repeat=len(endpoint_matrices)):
            state = policy_state.copy()
            labels = []
            for i, choice in enumerate(choices):
                label, M = endpoint_matrices[i][choice]
                state = state @ M
                labels.append(label)
                by_stage[AGES[i + 1]].append((state[1], "|".join(labels)))
        for age in AGES:
            values = [x[0] for x in by_stage[age]]
            rows.append(
                {
                    "assumed_initial_effect_delta": delta,
                    "age_stage": age,
                    "baseline_observed_occupancy": float(baseline.loc[age]),
                    "counterfactual_occupancy_lower": float(np.min(values)),
                    "counterfactual_occupancy_upper": float(np.max(values)),
                    "increment_lower": float(np.min(values) - baseline.loc[age]),
                    "increment_upper": float(np.max(values) - baseline.loc[age]),
                    "endpoint_paths_evaluated": len(values),
                }
            )

    pd.DataFrame(rows).to_csv(args.out_dir / "school_threshold_transition_envelopes.csv", index=False)
    (args.out_dir / "README.txt").write_text(
        "Counterfactual threshold envelope using NSS 76 sharp transition sets.\n"
        "The input delta is assumed, not estimated; delta=0 is a calibration check.\n"
        "Each later school-age occupancy is evaluated across all 8 endpoint combinations.\n"
        "This is not a causal forecast or an annual transition model.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
