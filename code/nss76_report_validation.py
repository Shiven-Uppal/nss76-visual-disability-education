#!/usr/bin/env python3
"""Reproduce selected published NSS 76 national estimates from official CSV data.

This is a pre-analysis validation gate.  It checks that the released CSV files,
the official final multiplier, and the published definitions give the national
estimates reported in NSS Report No. 583 (2019).  It is deliberately limited to
aggregate, non-disclosive outputs and makes no causal or transition claims.

Usage:
  python nss76_report_validation.py --raw-dir /path/to/CSV_PWD_76 --out-dir outputs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


# NSS Report No. 583, Statement 7 (p. 49) and Statement 35 (p. 77), all India.
# Values are reported to one decimal place; agreement after rounding is required.
PUBLISHED = {
    "preschool_intervention_age_3_35_pct": 10.1,
    "ever_enrolled_ordinary_school_age_3_35_pct": 62.9,
    "lfpr_age_15_plus_pct": 23.8,
    "wpr_age_15_plus_pct": 22.8,
    "unemployment_rate_age_15_plus_pct": 4.2,
}
WORK_CODES = {11, 12, 21, 31, 41, 51}


def weighted_share(numerator: pd.Series, weights: pd.Series) -> float:
    """Return a multiplier-weighted percentage, with explicit denominator checks."""
    denominator = weights.sum()
    if denominator <= 0:
        raise ValueError("Non-positive weighted denominator.")
    return 100 * weights.loc[numerator].sum() / denominator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    school = pd.read_csv(
        args.raw_dir / "Block 7 Level 13.csv",
        usecols=[
            "Age_years_col_2_block_5",
            "Attended_preschool_intervent_pro",
            "Ever_enrolled_ordinary_school",
            "MULT",
        ],
        low_memory=False,
    )
    school = school.loc[school["Age_years_col_2_block_5"].between(3, 35)].copy()
    if school.empty:
        raise ValueError("No age 3–35 records found in Block 7.")

    labour = pd.read_csv(
        args.raw_dir / "Block 8 Level 14.csv",
        usecols=[
            "Age_years_col_2_block_5",
            "Usual_principal_activity_status",
            "Usual_subsid_eco_activity_status",
            "MULT",
        ],
        low_memory=False,
    )
    labour = labour.loc[labour["Age_years_col_2_block_5"] >= 15].copy()
    if labour.empty:
        raise ValueError("No age 15+ records found in Block 8.")

    # Statement 35 defines usual status (ps+ss): employed if a person worked in
    # either usual principal or subsidiary status.  A principal-status unemployed
    # person remains unemployed only if they did not work in subsidiary status.
    principal = labour["Usual_principal_activity_status"]
    subsidiary = labour["Usual_subsid_eco_activity_status"]
    employed = principal.isin(WORK_CODES) | subsidiary.isin(WORK_CODES)
    unemployed = principal.eq(81) & ~subsidiary.isin(WORK_CODES)
    labour_force = employed | unemployed
    if not labour_force.any():
        raise ValueError("No labour-force observations under the documented status rule.")

    observed = {
        "preschool_intervention_age_3_35_pct": weighted_share(
            school["Attended_preschool_intervent_pro"].eq(1), school["MULT"]
        ),
        "ever_enrolled_ordinary_school_age_3_35_pct": weighted_share(
            school["Ever_enrolled_ordinary_school"].eq(1), school["MULT"]
        ),
        "lfpr_age_15_plus_pct": weighted_share(labour_force, labour["MULT"]),
        "wpr_age_15_plus_pct": weighted_share(employed, labour["MULT"]),
        "unemployment_rate_age_15_plus_pct": 100
        * labour.loc[unemployed, "MULT"].sum()
        / labour.loc[labour_force, "MULT"].sum(),
    }

    validation = pd.DataFrame(
        {
            "indicator": PUBLISHED.keys(),
            "published_percent": PUBLISHED.values(),
            "computed_percent": [observed[key] for key in PUBLISHED],
        }
    )
    validation["computed_rounded_1dp"] = validation["computed_percent"].round(1)
    validation["passes_published_rounding"] = (
        validation["computed_rounded_1dp"] == validation["published_percent"]
    )
    validation.to_csv(args.out_dir / "published_estimate_validation.csv", index=False)

    denominators = pd.DataFrame(
        [
            ("education_age_3_35", len(school), school["MULT"].sum()),
            ("labour_age_15_plus", len(labour), labour["MULT"].sum()),
            ("labour_force_age_15_plus", int(labour_force.sum()), labour.loc[labour_force, "MULT"].sum()),
        ],
        columns=["analytic_denominator", "unweighted_n", "weighted_population"],
    )
    denominators.to_csv(args.out_dir / "validation_denominators.csv", index=False)

    status = "PASS" if validation["passes_published_rounding"].all() else "FAIL"
    (args.out_dir / "README.txt").write_text(
        "NSS 76 published-estimate validation gate\n"
        f"Status: {status}\n\n"
        "Benchmarks: NSS Report No. 583, Statement 7 (p. 49) and Statement 35 (p. 77).\n"
        "Weights: final multiplier (MULT) supplied in the relevant official block.\n"
        "This validates selected national point estimates only; it does not validate\n"
        "standard errors, causal identification, transition assumptions, or a Markov model.\n",
        encoding="utf-8",
    )
    if status != "PASS":
        raise SystemExit("Published-estimate validation failed; do not proceed to modelling.")


if __name__ == "__main__":
    main()
