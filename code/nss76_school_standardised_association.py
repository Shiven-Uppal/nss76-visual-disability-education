#!/usr/bin/env python3
"""Common-support standardised schooling association for NSS 76 visual disability.

This is an adjusted descriptive association, not a causal effect. It compares
ordinary-school enrolment by observed pre-school-intervention history after
direct standardisation over prespecified baseline strata. Design uncertainty is
obtained by resampling PSUs within *full Block-1* strata, retaining PSUs with
zero visual-disability records in the resampling frame.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


KEY = ["HHID", "person_serial"]


def add_design_ids(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["design_stratum"] = out[["StateCode", "Sector", "Stratum", "Sub_stratum"]].astype(str).agg("|".join, axis=1)
    out["psu"] = out["design_stratum"] + "|" + out["FSU_Serial_No"].astype(str)
    return out


def weighted_cutpoints(x: pd.Series, w: pd.Series, probabilities: list[float]) -> list[float]:
    order = np.argsort(x.to_numpy())
    xv, wv = x.to_numpy()[order], w.to_numpy()[order]
    cumulative = np.cumsum(wv) / wv.sum()
    return [float(xv[np.searchsorted(cumulative, probability, side="left")]) for probability in probabilities]


def standardised_difference(data: pd.DataFrame, weights: np.ndarray) -> tuple[float, float, float, float]:
    """Return p(no support), p(support), difference and common-support coverage."""
    t = data[["cell", "support", "ordinary_school"]].copy()
    t["w"] = weights
    grouped = t.groupby(["cell", "support"], observed=True).apply(
        lambda g: pd.Series({"population": g.w.sum(), "event_population": (g.w * g.ordinary_school).sum()}),
        include_groups=False,
    ).reset_index()
    rates = grouped.pivot(index="cell", columns="support", values=["population", "event_population"])
    rates.columns = [f"{a}_{b}" for a, b in rates.columns]
    required = ["population_0", "population_1", "event_population_0", "event_population_1"]
    rates = rates.dropna(subset=required)
    rates = rates.loc[(rates["population_0"] > 0) & (rates["population_1"] > 0)].copy()
    if rates.empty:
        raise ValueError("No common support across the prespecified baseline cells.")
    cell_population = (rates["population_0"] + rates["population_1"])
    p0 = np.average(rates["event_population_0"] / rates["population_0"], weights=cell_population)
    p1 = np.average(rates["event_population_1"] / rates["population_1"], weights=cell_population)
    in_common = data["cell"].isin(rates.index)
    coverage = weights[in_common.to_numpy()].sum() / weights.sum()
    return float(p0), float(p1), float(p1 - p0), float(coverage)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=200)
    parser.add_argument("--seed", type=int, default=76026)
    parser.add_argument("--min-age", type=int, default=3)
    parser.add_argument("--max-age", type=int, default=35)
    parser.add_argument("--output-name", default="school_standardised_association.csv")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    visual = pd.read_csv(args.raw_dir / "Block 5_2 Level 6.csv", usecols=["HHID", "Srl_col1block_5", "Age_years_col_2_block_5", "Category_of_disability", "MULT", "StateCode", "Sector", "Stratum", "Sub_stratum", "FSU_Serial_No"], low_memory=False).rename(columns={"Srl_col1block_5": "person_serial", "Age_years_col_2_block_5": "age_visual"})
    person = pd.read_csv(args.raw_dir / "Block_3_Level _2.csv", usecols=["HHID", "Person_Srl_No", "Age", "Gender"], low_memory=False).rename(columns={"Person_Srl_No": "person_serial", "Age": "age_person"})
    household = pd.read_csv(args.raw_dir / "Block 4 Level 3.csv", usecols=["HHID", "Usual_monthly_consumer_expenditu"], low_memory=False)
    school = pd.read_csv(args.raw_dir / "Block 7 Level 13.csv", usecols=["HHID", "Srl_col1block_5", "Attended_preschool_intervent_pro", "Ever_enrolled_ordinary_school"], low_memory=False).rename(columns={"Srl_col1block_5": "person_serial"})
    frame = pd.read_csv(args.raw_dir / "Block 1 Level 1.csv", usecols=["StateCode", "Sector", "Stratum", "Sub_stratum", "FSU_Serial_No"], low_memory=False).drop_duplicates()

    data = visual.merge(person, on=KEY, validate="one_to_one").merge(household, on="HHID", validate="many_to_one").merge(school, on=KEY, validate="one_to_one")
    data = add_design_ids(data)
    frame = add_design_ids(frame)
    data = data.loc[
        data.age_visual.eq(data.age_person)
        & data.age_person.between(args.min_age, args.max_age)
        & data.Gender.isin([1, 2])
        & data.Category_of_disability.isin([1, 2, 3, 4, 5])
        & data.Attended_preschool_intervent_pro.isin([1, 2])
        & data.Ever_enrolled_ordinary_school.isin([1, 2])
        & (data.Usual_monthly_consumer_expenditu > 0)
    ].copy()
    data["support"] = data.Attended_preschool_intervent_pro.eq(1).astype(int)
    data["ordinary_school"] = data.Ever_enrolled_ordinary_school.eq(1).astype(int)
    if args.max_age <= 17:
        data["age_band"] = pd.cut(
            data.age_person,
            [args.min_age - 1, 10, args.max_age],
            labels=[f"{args.min_age}-10", "11-17"],
            include_lowest=True,
        ).astype(str)
    else:
        data["age_band"] = pd.cut(
            data.age_person,
            [args.min_age - 1, 10, 17, args.max_age],
            labels=[f"{args.min_age}-10", "11-17", "18-35"],
            include_lowest=True,
        ).astype(str)
    data["severity_band"] = data.Category_of_disability.map({1: "no_light", 2: "up_to_3ft", 3: "up_to_3ft", 4: "3_to_10ft", 5: "3_to_10ft"})
    q1, q2 = weighted_cutpoints(data.Usual_monthly_consumer_expenditu, data.MULT, [1 / 3, 2 / 3])
    data["mpce_tertile"] = pd.cut(data.Usual_monthly_consumer_expenditu, [-np.inf, q1, q2, np.inf], labels=["low", "middle", "high"], include_lowest=True).astype(str)
    data["cell"] = data[["age_band", "Gender", "Sector", "severity_band", "mpce_tertile"]].astype(str).agg("|".join, axis=1)

    base_w = data.MULT.to_numpy(dtype=float)
    p0, p1, diff, coverage = standardised_difference(data, base_w)
    groups = frame.groupby("design_stratum", sort=False)["psu"].unique().to_list()
    rng = np.random.default_rng(args.seed)
    replicates: list[float] = []
    for _ in range(args.replicates):
        multipliers: dict[str, int] = {}
        for psus in groups:
            counts = pd.Series(rng.choice(psus, size=len(psus), replace=True)).value_counts()
            multipliers.update({str(k): int(v) for k, v in counts.items()})
        rw = base_w * data.psu.map(multipliers).fillna(0).to_numpy(dtype=float)
        try:
            replicates.append(standardised_difference(data, rw)[2])
        except ValueError:
            pass
    reps = np.asarray(replicates)
    if len(reps) < 0.95 * args.replicates:
        raise RuntimeError(f"Only {len(reps)} of {args.replicates} replicate estimates were valid.")

    results = pd.DataFrame([{
        "estimand": "common-support standardised association: pre-school intervention history versus ordinary-school enrolment",
        "age_lower": args.min_age,
        "age_upper": args.max_age,
        "analytic_n": len(data),
        "weighted_population": base_w.sum(),
        "common_support_weight_coverage": coverage,
        "adjusted_probability_no_intervention": p0,
        "adjusted_probability_intervention": p1,
        "adjusted_difference_percentage_points": 100 * diff,
        "bootstrap_se_percentage_points": 100 * reps.std(ddof=1),
        "bootstrap_ci95_low_percentage_points": 100 * np.quantile(reps, 0.025),
        "bootstrap_ci95_high_percentage_points": 100 * np.quantile(reps, 0.975),
        "bootstrap_replicates": len(reps),
    }])
    results.to_csv(args.out_dir / args.output_name, index=False)
    pd.DataFrame({"weighted_mpce_tertile_cutpoint": ["q33", "q67"], "rupees_per_month": [q1, q2]}).to_csv(args.out_dir / f"school_association_cutpoints_{args.min_age}_{args.max_age}.csv", index=False)
    (args.out_dir / "README.txt").write_text(
        "NSS 76 standardised school association, detailed visual-disability population.\n"
        "Adjustment cells: age band, sex, rural/urban sector, visual-severity band, weighted household-expenditure tertile.\n"
        "The comparison is restricted to common support and is an adjusted association, not a causal effect.\n"
        "Bootstrap resamples PSUs in full Block-1 design strata and retains domain-zero PSUs.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
