#!/usr/bin/env python3
"""Design-aware robustness analyses for the NSS-76 visual-disability manuscript.

Outputs four analysis products, all based on the released NSS-76 microdata:
1. PSU-bootstrap uncertainty intervals for sharp transition bounds and the
   conditional school-participation envelope.
2. A one-year boundary-shift sensitivity analysis for the 6--14 age stages.
3. Pre-standardisation covariate balance and the common target distribution
   induced by direct standardisation.

No result is interpreted as a causal intervention effect.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


KEY = ["HHID", "person_serial"]
BASE_AGES = [("3-5", 3, 5), ("6-10", 6, 10), ("11-14", 11, 14),
             ("15-17", 15, 17)]
ALT_AGES = [("3-5", 3, 5), ("6-11", 6, 11), ("12-14", 12, 14),
            ("15-17", 15, 17)]


def add_design_ids(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["design_stratum"] = out[["StateCode", "Sector", "Stratum", "Sub_stratum"]].astype(str).agg("|".join, axis=1)
    out["psu"] = out["design_stratum"] + "|" + out["FSU_Serial_No"].astype(str)
    return out


def weighted_cutpoints(x: pd.Series, w: pd.Series, probabilities: list[float]) -> list[float]:
    order = np.argsort(x.to_numpy())
    xv, wv = x.to_numpy()[order], w.to_numpy()[order]
    cumulative = np.cumsum(wv) / wv.sum()
    return [float(xv[np.searchsorted(cumulative, p, side="left")]) for p in probabilities]


def weighted_occupancies(data: pd.DataFrame, weights: np.ndarray, ages: list[tuple[str, int, int]]) -> np.ndarray:
    vals = []
    for _, lo, hi in ages:
        mask = data.age_person.between(lo, hi).to_numpy()
        w = weights[mask]
        vals.append(float(np.dot(w, data.loc[mask, "ordinary_school_current"]) / w.sum()))
    return np.asarray(vals)


def transition_bounds(m0: float, m1: float) -> tuple[float, float, float, float]:
    e_lo = max(0.0, (m1 - m0) / (1.0 - m0))
    e_hi = min(1.0, m1 / (1.0 - m0))
    d_lo = max(0.0, (m0 - m1) / m0)
    d_hi = min(1.0, (1.0 - m1) / m0)
    return e_lo, e_hi, d_lo, d_hi


def envelope_from_occupancies(m: np.ndarray, delta: float) -> tuple[np.ndarray, np.ndarray]:
    """Exact endpoint envelope for a two-state sharp transition set."""
    pairs = []
    for m0, m1 in zip(m[:-1], m[1:]):
        e_lo, e_hi, d_lo, d_hi = transition_bounds(float(m0), float(m1))
        # Endpoints of the feasible line segment; pairs must remain coupled.
        pairs.append(((e_lo, d_lo), (e_hi, d_hi)))
    lows, highs = [m[0] + delta], [m[0] + delta]
    states = [m[0] + delta]
    for stage in range(len(pairs)):
        next_states = []
        for state in states:
            for e, d in pairs[stage]:
                next_states.append((1.0 - state) * e + state * (1.0 - d))
        lows.append(min(next_states))
        highs.append(max(next_states))
        states = next_states
    return np.asarray(lows), np.asarray(highs)


def bootstrap_dynamic(data: pd.DataFrame, frame: pd.DataFrame, replicates: int, seed: int, delta: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    base_w = data.MULT.to_numpy(float)
    m_point = weighted_occupancies(data, base_w, BASE_AGES)
    low_point, high_point = envelope_from_occupancies(m_point, delta)
    groups = frame.groupby("design_stratum", sort=False)["psu"].unique().to_list()
    rng = np.random.default_rng(seed)
    bnd = []
    env = []
    for b in range(replicates):
        multiplicities: dict[str, int] = {}
        for psus in groups:
            sampled = pd.Series(rng.choice(psus, size=len(psus), replace=True)).value_counts()
            multiplicities.update({str(k): int(v) for k, v in sampled.items()})
        rw = base_w * data.psu.map(multiplicities).fillna(0).to_numpy(float)
        m = weighted_occupancies(data, rw, BASE_AGES)
        lo, hi = envelope_from_occupancies(m, delta)
        for (from_label, _, _), (to_label, _, _), m0, m1 in zip(BASE_AGES[:-1], BASE_AGES[1:], m[:-1], m[1:]):
            e_lo, e_hi, d_lo, d_hi = transition_bounds(float(m0), float(m1))
            bnd.append((b, from_label, to_label, e_lo, e_hi, d_lo, d_hi))
        for (label, _, _), xlo, xhi in zip(BASE_AGES, lo, hi):
            env.append((b, label, xlo, xhi))
    bnd_df = pd.DataFrame(bnd, columns=["replicate", "from_age_stage", "to_age_stage", "entry_lower", "entry_upper", "exit_lower", "exit_upper"])
    env_df = pd.DataFrame(env, columns=["replicate", "age_stage", "counterfactual_lower", "counterfactual_upper"])
    bound_rows = []
    for (from_label, _, _), (to_label, _, _) in zip(BASE_AGES[:-1], BASE_AGES[1:]):
        d = bnd_df.loc[(bnd_df.from_age_stage == from_label) & (bnd_df.to_age_stage == to_label)]
        point = transition_bounds(float(m_point[list(x[0] for x in BASE_AGES).index(from_label)]), float(m_point[list(x[0] for x in BASE_AGES).index(to_label)]))
        row = {"from_age_stage": from_label, "to_age_stage": to_label, "bootstrap_replicates": replicates}
        for name, val in zip(["entry_lower", "entry_upper", "exit_lower", "exit_upper"], point):
            row[f"{name}_point"] = val
            row[f"{name}_bootstrap_ci95_low"] = float(d[name].quantile(0.025))
            row[f"{name}_bootstrap_ci95_high"] = float(d[name].quantile(0.975))
        bound_rows.append(row)
    env_rows = []
    for idx, (label, _, _) in enumerate(BASE_AGES):
        d = env_df.loc[env_df.age_stage == label]
        env_rows.append({
            "assumed_initial_effect_delta": delta,
            "age_stage": label,
            "baseline_occupancy_point": m_point[idx],
            "envelope_lower_point": low_point[idx],
            "envelope_upper_point": high_point[idx],
            "envelope_lower_bootstrap_ci95_low": float(d.counterfactual_lower.quantile(0.025)),
            "envelope_lower_bootstrap_ci95_high": float(d.counterfactual_lower.quantile(0.975)),
            "envelope_upper_bootstrap_ci95_low": float(d.counterfactual_upper.quantile(0.025)),
            "envelope_upper_bootstrap_ci95_high": float(d.counterfactual_upper.quantile(0.975)),
            "bootstrap_replicates": replicates,
        })
    return pd.DataFrame(bound_rows), pd.DataFrame(env_rows)


def age_band_sensitivity(data: pd.DataFrame, delta: float) -> pd.DataFrame:
    base_w = data.MULT.to_numpy(float)
    rows = []
    for specification, ages in [("primary specification", BASE_AGES), ("one-year shifted 6-14 boundary", ALT_AGES)]:
        m = weighted_occupancies(data, base_w, ages)
        lo, hi = envelope_from_occupancies(m, delta)
        for (label, start, end), occ, lower, upper in zip(ages, m, lo, hi):
            rows.append({"age_band_specification": specification, "age_stage": label, "lower_age": start, "upper_age": end,
                         "weighted_occupancy": occ, "counterfactual_lower": lower, "counterfactual_upper": upper,
                         "increment_lower": lower-occ, "increment_upper": upper-occ, "assumed_initial_effect_delta": delta})
    return pd.DataFrame(rows)


def standardised_balance(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = data.loc[
        data.age_person.between(3, 35) & data.Gender.isin([1, 2]) & data.Category_of_disability.isin([1, 2, 3, 4, 5])
        & data.Attended_preschool_intervent_pro.isin([1, 2]) & data.Ever_enrolled_ordinary_school.isin([1, 2])
        & (data.Usual_monthly_consumer_expenditu > 0)
    ].copy()
    d["support"] = d.Attended_preschool_intervent_pro.eq(1).astype(int)
    d["age_band"] = pd.cut(d.age_person, [2, 10, 17, 35], labels=["3-10", "11-17", "18-35"], include_lowest=True).astype(str)
    d["severity_band"] = d.Category_of_disability.map({1:"no_light", 2:"up_to_3ft", 3:"up_to_3ft", 4:"3_to_10ft", 5:"3_to_10ft"})
    q1, q2 = weighted_cutpoints(d.Usual_monthly_consumer_expenditu, d.MULT, [1/3, 2/3])
    d["mpce_tertile"] = pd.cut(d.Usual_monthly_consumer_expenditu, [-np.inf, q1, q2, np.inf], labels=["low", "middle", "high"], include_lowest=True).astype(str)
    covariates = ["age_band", "Gender", "Sector", "severity_band", "mpce_tertile"]
    d["cell"] = d[covariates].astype(str).agg("|".join, axis=1)
    cell_support = d.groupby(["cell", "support"], observed=True).MULT.sum().unstack(fill_value=0)
    common_cells = cell_support.index[(cell_support.get(0, 0) > 0) & (cell_support.get(1, 0) > 0)]
    d = d.loc[d.cell.isin(common_cells)].copy()
    # Direct-standardisation target: pooled common-support cell population.
    target = d.groupby("cell", observed=True).MULT.sum()
    target = target / target.sum()
    cell_meta = d.drop_duplicates("cell").set_index("cell")
    rows = []
    for var in covariates:
        for level in sorted(d[var].astype(str).unique()):
            p = {}
            for support in [0, 1]:
                g = d.loc[d.support.eq(support)]
                p[support] = float(g.loc[g[var].astype(str).eq(level), "MULT"].sum() / g.MULT.sum())
            denom = np.sqrt((p[0]*(1-p[0]) + p[1]*(1-p[1]))/2)
            smd = 0.0 if denom == 0 else (p[1]-p[0])/denom
            # Every covariate in the cell definition is balanced exactly under this target.
            target_pct = float(target[cell_meta.loc[target.index, var].astype(str).eq(level)].sum())
            rows.append({"covariate": var, "level": level, "no_intervention_weighted_percent": 100*p[0],
                         "intervention_weighted_percent": 100*p[1], "pre_standardisation_smd": smd,
                         "standardised_target_percent": 100*target_pct, "post_standardisation_smd": 0.0})
    summary = pd.DataFrame([{"analytic_n": len(d), "weighted_population": d.MULT.sum(),
                             "common_support_weighted_coverage": d.MULT.sum()/data.loc[data.age_person.between(3,35) & data.Gender.isin([1,2]) & data.Category_of_disability.isin([1,2,3,4,5]) & data.Attended_preschool_intervent_pro.isin([1,2]) & data.Ever_enrolled_ordinary_school.isin([1,2]) & (data.Usual_monthly_consumer_expenditu>0), "MULT"].sum(),
                             "mpce_q33": q1, "mpce_q67": q2}])
    return pd.DataFrame(rows), summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--replicates", type=int, default=999)
    ap.add_argument("--seed", type=int, default=76026)
    ap.add_argument("--delta", type=float, default=0.10)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    v = pd.read_csv(args.raw_dir / "Block 5_2 Level 6.csv", usecols=["HHID","Srl_col1block_5","Age_years_col_2_block_5","Category_of_disability","MULT","StateCode","Sector","Stratum","Sub_stratum","FSU_Serial_No"], low_memory=False).rename(columns={"Srl_col1block_5":"person_serial","Age_years_col_2_block_5":"age_visual"})
    p = pd.read_csv(args.raw_dir / "Block_3_Level _2.csv", usecols=["HHID","Person_Srl_No","Age","Gender"], low_memory=False).rename(columns={"Person_Srl_No":"person_serial","Age":"age_person"})
    h = pd.read_csv(args.raw_dir / "Block 4 Level 3.csv", usecols=["HHID","Usual_monthly_consumer_expenditu"], low_memory=False)
    s = pd.read_csv(args.raw_dir / "Block 7 Level 13.csv", usecols=["HHID","Srl_col1block_5","Currently_attending_ordinary_sch","Attended_preschool_intervent_pro","Ever_enrolled_ordinary_school"], low_memory=False).rename(columns={"Srl_col1block_5":"person_serial"})
    frame = pd.read_csv(args.raw_dir / "Block 1 Level 1.csv", usecols=["StateCode","Sector","Stratum","Sub_stratum","FSU_Serial_No"], low_memory=False).drop_duplicates()
    data = v.merge(p,on=KEY,validate="one_to_one").merge(h,on="HHID",validate="many_to_one").merge(s,on=KEY,how="left",validate="one_to_one")
    data = add_design_ids(data.loc[data.age_visual.eq(data.age_person)].copy())
    frame = add_design_ids(frame)
    data["ordinary_school_current"] = data.Currently_attending_ordinary_sch.eq(1).astype(int)
    school = data.loc[data.age_person.between(3,35)].copy()
    bounds, envelopes = bootstrap_dynamic(school, frame, args.replicates, args.seed, args.delta)
    sensitivity = age_band_sensitivity(school, args.delta)
    balance, balance_summary = standardised_balance(data)
    bounds.to_csv(args.out_dir / "dynamic_transition_bounds_bootstrap.csv", index=False)
    envelopes.to_csv(args.out_dir / "dynamic_envelope_bootstrap.csv", index=False)
    sensitivity.to_csv(args.out_dir / "age_band_sensitivity.csv", index=False)
    balance.to_csv(args.out_dir / "standardised_covariate_balance.csv", index=False)
    balance_summary.to_csv(args.out_dir / "standardised_covariate_balance_summary.csv", index=False)
    (args.out_dir / "README.txt").write_text(
        f"Design-aware robustness analysis. {args.replicates} PSU bootstrap replicates, seed {args.seed}; assumed initial scenario delta={args.delta:.2f}.\n"
        "Bootstrap intervals describe sampling uncertainty in estimated sharp-set bounds/envelopes, not causal uncertainty.\n"
        "The age-band sensitivity shifts the 6--14 boundary by one year; it is a structural robustness diagnostic.\n"
        "Post-standardisation balance is zero by construction because all listed covariates define the direct-standardisation cells.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
