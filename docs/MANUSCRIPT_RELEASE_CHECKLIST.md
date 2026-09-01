# Manuscript-ready release checklist

The manuscript-ready release will be tagged `v1.0.0` only after the following public materials have been added.

## 1. Analysis code

Upload the scripts or notebooks used to produce the analysis. Do **not** upload NSS-76 microdata.

Suggested contents:

- `01_import_and_clean.*`
- `02_construct_variables.*`
- `03_standardised_association.*`
- `04_markov_bounds.*`
- `05_sensitivity_analyses.*`
- `06_tables_and_figures.*`
- `README.md` stating the required software version and package dependencies.

If the original analysis was conducted interactively, add a single script that recreates every reported result from authorised raw data.

## 2. Variable dictionary

For each analytic variable, document:

| Required field | Example |
| --- | --- |
| Analysis variable | `ordinary_school_current` |
| Source field(s) | Exact NSS-76 name(s) |
| Definition | Current participation in an ordinary school |
| Coding | 1 = yes; 0 = no |
| Eligible population | Persons with visual disability in the relevant age range |
| Used in | Main association / age-stage model / sensitivity analysis |

The exact NSS-76 source-field names must be checked against the authorised data and code. Do not guess or infer them from labels alone.

## 3. Public derived aggregate estimates

Add only non-disclosive aggregates. At minimum include:

- analytic sample count;
- weighted common-support coverage;
- standardised probabilities by reported intervention status;
- adjusted percentage-point difference;
- PSU-bootstrap 95% interval;
- age-stage occupancy estimates and transition bounds; and
- Supplementary Table S1.

### Supplementary Table S1

| Analytic population | Unweighted eligible records | Weighted common-support coverage | Standardised probability: no reported intervention | Standardised probability: reported intervention | Adjusted percentage-point difference | PSU-bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ages 3–35 (main analysis) | 2,721 | 89.55% | 53.61% | 85.25% | 31.64 | 27.71 to 36.26 |
| Ages 3–17 | To be computed | To be computed | To be computed | To be computed | To be computed | To be computed |
| Ages 6–17 | To be computed | To be computed | To be computed | To be computed | To be computed | To be computed |

The two restricted-age rows require rerunning the analysis; they cannot be obtained validly from the existing main-analysis numbers alone.

## Before publishing v1.0.0

- [ ] Raw NSS-76 data and respondent-level extracts are absent.
- [ ] Code runs from a fresh authorised-data copy.
- [ ] Source field names in the dictionary match the code.
- [ ] Supplementary Table S1 contains computed—not placeholder—values.
- [ ] The manuscript's repository link is correct.
- [ ] Create the `v1.0.0` release and use its new Zenodo DOI in the manuscript.
