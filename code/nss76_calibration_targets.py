#!/usr/bin/env python3
"""Extract validated, weighted NSS 76 occupancy targets for policy-model calibration.

Targets are cross-sectional outcome occupancies. They constrain a calibrated
cohort model but do not identify individual annual transition probabilities.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


KEY = ["HHID", "person_serial"]


def rate_by_age(data: pd.DataFrame, outcome: str, groups: list[tuple[str, int, int]]) -> list[dict[str, float | int | str]]:
    rows = []
    for label, low, high in groups:
        d = data.loc[data.age_person.between(low, high)]
        rows.append({
            "target": outcome,
            "age_band": label,
            "unweighted_n": len(d),
            "weighted_population": d.MULT.sum(),
            "weighted_probability": (d.MULT * d[outcome]).sum() / d.MULT.sum() if len(d) else np.nan,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    v = pd.read_csv(args.raw_dir / "Block 5_2 Level 6.csv", usecols=["HHID", "Srl_col1block_5", "Age_years_col_2_block_5", "MULT"], low_memory=False).rename(columns={"Srl_col1block_5": "person_serial", "Age_years_col_2_block_5": "age_visual"})
    p = pd.read_csv(args.raw_dir / "Block_3_Level _2.csv", usecols=["HHID", "Person_Srl_No", "Age", "Highest_level_education"], low_memory=False).rename(columns={"Person_Srl_No": "person_serial", "Age": "age_person"})
    s = pd.read_csv(args.raw_dir / "Block 7 Level 13.csv", usecols=["HHID", "Srl_col1block_5", "Currently_attending_ordinary_sch"], low_memory=False).rename(columns={"Srl_col1block_5": "person_serial"})
    l = pd.read_csv(args.raw_dir / "Block 8 Level 14.csv", usecols=["HHID", "Srl_col1block_5", "Usual_principal_activity_status", "Usual_subsid_eco_activity_status"], low_memory=False).rename(columns={"Srl_col1block_5": "person_serial"})
    d = v.merge(p, on=KEY, validate="one_to_one").merge(s, on=KEY, how="left", validate="one_to_one").merge(l, on=KEY, how="left", validate="one_to_one")
    d = d.loc[d.age_visual.eq(d.age_person)].copy()
    d["ordinary_school_current"] = d.Currently_attending_ordinary_sch.eq(1).astype(int)
    d["secondary_or_above"] = d.Highest_level_education.isin([10, 11, 12, 13, 14, 15, 16]).astype(int)
    work = [11, 12, 21, 31, 41, 51]
    d["employed_psss"] = (d.Usual_principal_activity_status.isin(work) | d.Usual_subsid_eco_activity_status.isin(work)).astype(int)
    rows = []
    rows += rate_by_age(d.loc[d.age_person.between(3, 35)], "ordinary_school_current", [("3-5", 3, 5), ("6-10", 6, 10), ("11-14", 11, 14), ("15-17", 15, 17), ("18-24", 18, 24), ("25-35", 25, 35)])
    rows += rate_by_age(d.loc[d.age_person >= 15], "secondary_or_above", [("15-17", 15, 17), ("18-24", 18, 24), ("25-34", 25, 34), ("35-44", 35, 44), ("45-59", 45, 59), ("60+", 60, 125)])
    rows += rate_by_age(d.loc[d.age_person >= 15], "employed_psss", [("15-17", 15, 17), ("18-24", 18, 24), ("25-34", 25, 34), ("35-44", 35, 44), ("45-59", 45, 59), ("60+", 60, 125)])
    targets = pd.DataFrame(rows)
    targets.to_csv(args.out_dir / "nss76_visual_occupancy_calibration_targets.csv", index=False)
    (args.out_dir / "README.txt").write_text(
        "Validated NSS 76 outcome-occupancy targets for detailed visual disability.\n"
        "Use only as weighted cross-sectional calibration targets, not as annual transitions or causal effects.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
