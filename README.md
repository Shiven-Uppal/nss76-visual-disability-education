# NSS-76 Visual-Disability Education Analysis

Reproducibility materials for *Early Educational Support and Ordinary-School Participation among Persons with Visual Disability in India: NSS-76 Evidence and a Partially Identified Age-Stage Markov Framework*.

## Contents

- `code/` — Python scripts that reproduce the public aggregate outputs from authorised NSS-76 data.
- `derived_aggregates/` — non-disclosive aggregate tables, including the age-restricted sensitivity analysis.
- `data_dictionary/variable_dictionary.md` — source-variable mapping and analytic definitions.
- `docs/REPRODUCIBILITY.md` — data-access and reproducibility documentation.
- `docs/MANUSCRIPT_RELEASE_CHECKLIST.md` — release checklist.
- `docs/MANUSCRIPT_INSERTIONS.md` — manuscript-ready wording and Supplementary Table S1.

## Restricted source data

This repository does **not** contain NSS-76 unit-level microdata, respondent-level extracts, or access credentials. The data must be obtained directly from the Ministry of Statistics and Programme Implementation's Online Microdata Library, subject to its data-access terms.

## Software

Python 3.11+ with the packages in `requirements.txt`.

The scripts are written for the official NSS-76 CSV release. Place authorised source files in a local directory that is outside version control, then run:

```text
python code/nss76_school_standardised_association.py --raw-dir /path/to/nss76-csv --out-dir derived_aggregates
python code/nss76_school_standardised_association.py --raw-dir /path/to/nss76-csv --out-dir derived_aggregates --min-age 3 --max-age 17 --output-name school_standardised_association_3_17.csv
python code/nss76_school_standardised_association.py --raw-dir /path/to/nss76-csv --out-dir derived_aggregates --min-age 6 --max-age 17 --output-name school_standardised_association_6_17.csv
python code/nss76_calibration_targets.py --raw-dir /path/to/nss76-csv --out-dir derived_aggregates
python code/nss76_partially_identified_markov.py --targets derived_aggregates/nss76_visual_occupancy_calibration_targets.csv --out-dir derived_aggregates
python code/nss76_threshold_markov_envelopes.py --targets derived_aggregates/nss76_visual_occupancy_calibration_targets.csv --transition-sets derived_aggregates/partially_identified_markov_transition_sets.csv --out-dir derived_aggregates
python code/nss76_robustness_analyses.py --raw-dir /path/to/nss76-csv --out-dir derived_aggregates --replicates 999
```

The main and age-restricted association analyses use 200 PSU-within-stratum bootstrap resamples, matching the manuscript. The dynamic analysis uses 999 resamples.

## Interpretation boundary

The results are survey-weighted descriptive estimates, adjusted non-causal associations, and sharp age-stage bounds. They do not identify an intervention effect, individual annual transition probabilities, an ICER, net present value, or return on investment.
