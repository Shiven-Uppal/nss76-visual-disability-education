# Analysis specification

This document records the analytic procedure described in the accompanying manuscript. It is a public specification, not a substitute for the runnable scripts or authorised NSS-76 microdata.

## Data source and linked files

- Survey: NSS 76th Round, *Survey of Persons with Disabilities* (July–December 2018).
- Visual-disability module: Block 5.2, Level 6 (`R76260L06`).
- Education module: Block 7, Level 13 (`R76260L13`).
- Supporting linked modules: person demographics, household characteristics, and official household/person identifiers.
- Weight: official final survey multiplier.

The exact source-field names and link keys must be read directly from the authorised NSS layout/codebook and then recorded in `data_dictionary/variable_dictionary.md`.

## Analytic populations

1. **Descriptive visual-disability population:** persons classified as having visual disability, restricted to valid information for the relevant outcome.
2. **Main support-associated analysis:** persons aged 3–35 years with visual disability and valid information on reported pre-school intervention, ever ordinary-school enrolment, and the adjustment variables.
3. **School-age dynamic analysis:** persons aged 3–17 years with visual disability, grouped into ages 3–5, 6–10, 11–14, and 15–17.
4. **Sensitivity populations:** persons aged 3–17 years and 6–17 years, respectively.

## Main association

- Exposure: reported participation in the NSS-recorded pre-school intervention programme.
- Outcome: ever ordinary-school enrolment.
- Adjustment variables: age band, sex, rural/urban sector, visual-disability severity, and household consumption-expenditure tertile.
- Estimand: survey-weighted direct-standardised difference in enrolment probability between reported intervention statuses, restricted to common support.
- Inference: PSU-within-stratum bootstrap.

The contrast is an adjusted association, not a causal effect.

## Dynamic bound calculation

Let `m_j` be the survey-weighted current ordinary-school participation rate at age stage `j`. For adjacent stages, feasible entry and exit parameters satisfy:

`m_(j+1) = (1 - m_j)e_j + m_j(1 - d_j)`

with `e_j,d_j ∈ [0,1]`. The procedure calculates sharp marginal bounds for each `e_j` and `d_j`, then evaluates the eight endpoint combinations across the three school-age transitions to obtain the counterfactual envelope under a stated initial participation change.

## Non-negotiable validation checks

- Reproduce selected all-disability benchmarks from NSS Report No. 583 before substantive modelling.
- Confirm analytic unweighted counts and weighted totals.
- Recalculate common support within each restricted-age sensitivity population.
- Record random seed, software version, and package versions.
- Never commit restricted microdata or respondent-level extracts.
