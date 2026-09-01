#!/usr/bin/env python3
"""Build a partially identified, age-stage Markov calibration from NSS 76 targets.

Repeated cross-sectional occupancies identify the marginal state prevalence at
each age stage, but not individual transition probabilities. For two states
(not in state, in state), this script reports the full feasible range of entry
and exit probabilities compatible with adjacent observed occupancies.

No association estimate is converted to a causal policy effect. A later policy
scenario must supply an externally justified intervention parameter.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


AGE_ORDER = {
    "ordinary_school_current": ["3-5", "6-10", "11-14", "15-17"],
}


def transition_set(m_current: float, m_next: float) -> dict[str, float]:
    """Sharp feasible set under m_next=(1-m)e+m(1-d), e,d in [0,1]."""
    if not (0 < m_current < 1 and 0 < m_next < 1):
        raise ValueError("Occupancies must lie strictly between 0 and 1.")
    entry_low = max(0.0, (m_next - m_current) / (1 - m_current))
    entry_high = min(1.0, m_next / (1 - m_current))
    # d is increasing in e in the marginal constraint.
    exit_low = (m_current + (1 - m_current) * entry_low - m_next) / m_current
    exit_high = (m_current + (1 - m_current) * entry_high - m_next) / m_current
    # A reference matrix with identical rows reproduces m_next exactly, but is
    # labelled a neutral calibration convention rather than a real transition estimate.
    entry_reference = m_next
    exit_reference = 1 - m_next
    return {
        "entry_lower": float(np.clip(entry_low, 0, 1)),
        "entry_upper": float(np.clip(entry_high, 0, 1)),
        "exit_lower": float(np.clip(exit_low, 0, 1)),
        "exit_upper": float(np.clip(exit_high, 0, 1)),
        "entry_neutral_reference": entry_reference,
        "exit_neutral_reference": exit_reference,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    targets = pd.read_csv(args.targets)
    all_rows: list[dict[str, float | str]] = []
    for state, ages in AGE_ORDER.items():
        subset = targets.loc[targets.target.eq(state)].set_index("age_band")
        missing = set(ages) - set(subset.index)
        if missing:
            raise ValueError(f"Missing {state} targets: {sorted(missing)}")
        for start, end in zip(ages[:-1], ages[1:]):
            m0 = float(subset.loc[start, "weighted_probability"])
            m1 = float(subset.loc[end, "weighted_probability"])
            row: dict[str, float | str] = {
                "state": state,
                "from_age_stage": start,
                "to_age_stage": end,
                "observed_occupancy_from": m0,
                "observed_occupancy_to": m1,
            }
            row.update(transition_set(m0, m1))
            all_rows.append(row)
    out = pd.DataFrame(all_rows)
    out.to_csv(args.out_dir / "partially_identified_markov_transition_sets.csv", index=False)
    (args.out_dir / "README.txt").write_text(
        "Partially identified age-stage Markov calibration from validated NSS 76 weighted occupancies.\n\n"
        "For each adjacent stage, e=P(not-in-state -> in-state) and d=P(in-state -> not-in-state) satisfy:\n"
        "m_next=(1-m_current)e+m_current(1-d). The CSV gives the sharp [0,1]-bounded set.\n"
        "The neutral reference matrix has identical rows and reproduces the next-stage marginal;\n"
        "it is a calibration convention, not evidence of individual persistence.\n"
        "Stage widths differ, so these are age-stage transitions, never annual transition estimates.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
