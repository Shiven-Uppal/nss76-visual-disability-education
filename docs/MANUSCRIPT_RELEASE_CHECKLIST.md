# Manuscript-ready release checklist

## Public materials now available

- [x] Python analysis scripts
- [x] Source-variable dictionary
- [x] Derived non-disclosive aggregate tables
- [x] Supplementary Table S1: age-restricted sensitivity analyses
- [x] School-age-only sharp transition sets and 999-resample dynamic uncertainty outputs
- [x] Data-access and reproducibility documentation

## Pre-release safeguards

- [x] No NSS-76 unit-level microdata or respondent-level extracts are in this repository.
- [x] The only potentially disclosive descriptive cell (a subgroup with fewer than 10 unweighted records) has been suppressed from the public aggregate table.
- [x] Main analysis and age-restricted sensitivity associations use 200 PSU-within-stratum bootstrap resamples.
- [x] Dynamic results use 999 PSU-within-stratum bootstrap resamples.

## Final step before submission

Create a GitHub release named `v1.0.0`. Zenodo will archive it and generate a new version DOI. Use that new DOI—not the earlier `v0.1.0` scaffold DOI—in the manuscript data-availability statement.
