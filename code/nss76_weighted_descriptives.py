#!/usr/bin/env python3
"""Create non-disclosive multiplier-weighted descriptive tables for NSS 76.

The analytic population is the linked detailed visual-disability block. These
are design-weighted point estimates only; uncertainty is produced separately.
No synthetic records are used or exported.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


KEY = ["HHID", "person_serial"]


def weighted_table(data: pd.DataFrame, variable: str, label: str, mapping: dict[int, str] | None = None) -> pd.DataFrame:
    temp = data[[variable, "MULT"]].copy()
    temp[variable] = temp[variable].fillna(-999).astype(int)
    out = temp.groupby(variable, dropna=False).agg(unweighted_n=("MULT", "size"), weighted_population=("MULT", "sum")).reset_index()
    out["weighted_percent"] = 100 * out["weighted_population"] / out["weighted_population"].sum()
    out.insert(0, "table", label)
    out = out.rename(columns={variable: "code"})
    out["category"] = out["code"].map(mapping or {}).fillna(out["code"].astype(str))
    return out[["table", "code", "category", "unweighted_n", "weighted_population", "weighted_percent"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    visual = pd.read_csv(
        args.raw_dir / "Block 5_2 Level 6.csv",
        usecols=["HHID", "Srl_col1block_5", "Age_years_col_2_block_5", "Category_of_disability",
                 "Aid_appliance_advised", "Aid_appliance_regularly_used", "MULT", "Sector"], low_memory=False,
    ).rename(columns={"Srl_col1block_5": "person_serial", "Age_years_col_2_block_5": "age_visual"})
    person = pd.read_csv(
        args.raw_dir / "Block_3_Level _2.csv", usecols=["HHID", "Person_Srl_No", "Age", "Gender", "Highest_level_education"], low_memory=False,
    ).rename(columns={"Person_Srl_No": "person_serial", "Age": "age_person"})
    school = pd.read_csv(
        args.raw_dir / "Block 7 Level 13.csv", usecols=["HHID", "Srl_col1block_5", "Attended_preschool_intervent_pro", "Ever_enrolled_ordinary_school"], low_memory=False,
    ).rename(columns={"Srl_col1block_5": "person_serial"})
    labour = pd.read_csv(
        args.raw_dir / "Block 8 Level 14.csv", usecols=["HHID", "Srl_col1block_5", "Usual_principal_activity_status", "Usual_subsid_eco_activity_status"], low_memory=False,
    ).rename(columns={"Srl_col1block_5": "person_serial"})

    data = visual.merge(person, on=KEY, validate="one_to_one").merge(school, on=KEY, how="left", validate="one_to_one").merge(labour, on=KEY, how="left", validate="one_to_one")
    data["age_consistent"] = data["age_visual"].eq(data["age_person"])
    data["age_group"] = pd.cut(data["age_person"], bins=[-1, 2, 10, 17, 35, np.inf], labels=[1, 2, 3, 4, 5]).astype("float").fillna(-999).astype(int)
    data["secondary_or_above"] = data["Highest_level_education"].isin([10, 11, 12, 13, 14, 15, 16]).astype(int)
    data["employed_psss"] = (
        data["Usual_principal_activity_status"].isin([11, 12, 21, 31, 41, 51])
        | data["Usual_subsid_eco_activity_status"].isin([11, 12, 21, 31, 41, 51])
    ).astype(int)

    full = data.loc[data["age_consistent"]].copy()
    school_data = full.loc[full["age_person"].between(3, 35)].copy()
    labour_data = full.loc[full["age_person"] >= 15].copy()
    tables = [
        weighted_table(full, "age_group", "age group", {1: "0-2", 2: "3-10", 3: "11-17", 4: "18-35", 5: "36+"}),
        weighted_table(full, "Gender", "gender", {1: "male", 2: "female", 3: "transgender"}),
        weighted_table(full, "Sector", "sector", {1: "rural", 2: "urban"}),
        weighted_table(full, "Category_of_disability", "visual disability category", {1: "no light perception", 2: "light perception; cannot count fingers up to 3 ft; spectacles", 3: "light perception; cannot count fingers up to 3 ft; no spectacles", 4: "cannot count fingers 3-10 ft; spectacles", 5: "cannot count fingers 3-10 ft; no spectacles"}),
        weighted_table(full, "Aid_appliance_advised", "aid/appliance pathway", {1: "advised and acquired", 2: "not acquired: unaffordable", 3: "not acquired: unavailable", 4: "not acquired: other", 5: "not advised"}),
        weighted_table(full.loc[full["Aid_appliance_advised"].eq(1)], "Aid_appliance_regularly_used", "regular use among acquired aid", {1: "regular use", 2: "not regular use"}),
        weighted_table(school_data, "Attended_preschool_intervent_pro", "pre-school intervention, age 3-35", {1: "attended", 2: "did not attend"}),
        weighted_table(school_data, "Ever_enrolled_ordinary_school", "ever ordinary-school enrolment, age 3-35", {1: "ever enrolled", 2: "never enrolled"}),
        weighted_table(labour_data, "secondary_or_above", "secondary-or-above, age 15+", {1: "secondary or above", 0: "below secondary"}),
        weighted_table(labour_data, "employed_psss", "employed usual status (ps+ss), age 15+", {1: "employed", 0: "not employed"}),
    ]
    pd.concat(tables, ignore_index=True).to_csv(args.out_dir / "weighted_descriptive_tables.csv", index=False)

    cross = (
        school_data.loc[school_data["Attended_preschool_intervent_pro"].isin([1, 2]) & school_data["Ever_enrolled_ordinary_school"].isin([1, 2])]
        .groupby(["Attended_preschool_intervent_pro", "Ever_enrolled_ordinary_school"])
        .agg(unweighted_n=("MULT", "size"), weighted_population=("MULT", "sum"))
        .reset_index()
    )
    cross["row_percent"] = 100 * cross["weighted_population"] / cross.groupby("Attended_preschool_intervent_pro")["weighted_population"].transform("sum")
    cross.to_csv(args.out_dir / "preschool_by_ordinary_school_unadjusted.csv", index=False)

    flow = pd.DataFrame(
        [("detailed visual-disability records", len(data)), ("age-consistent linked visual records", len(full)), ("schooling domain age 3-35", len(school_data)), ("labour domain age 15+", len(labour_data))],
        columns=["analytic_stage", "unweighted_n"],
    )
    flow.to_csv(args.out_dir / "analytic_flow.csv", index=False)
    (args.out_dir / "README.txt").write_text(
        "NSS 76 Schedule 26.0, detailed visual-disability descriptive tables.\n"
        "Point estimates sum final multiplier (MULT); confidence intervals are not included here.\n"
        "School and labour domains use internally age-consistent linked records.\n"
        "The preschool-by-school cross-tab is unadjusted and cannot be interpreted causally.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
