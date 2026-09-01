# NSS-76 Visual-Disability Education Analysis

Reproducibility materials for:

> **Early Educational Support and Ordinary-School Participation among Persons with Visual Disability in India: NSS-76 Evidence and a Partially Identified Age-Stage Markov Framework**

## What this repository contains

- analysis code (to be added);
- a variable dictionary;
- derived, non-disclosive aggregate tables;
- reproducibility documentation; and
- materials needed to reproduce the manuscript's tables and figures from authorised NSS-76 access.

## What this repository does not contain

This repository does **not** contain NSS-76 unit-level microdata, personally identifying information, or any restricted-data extracts. Those data cannot be redistributed here under the applicable access terms.

## Data access

The NSS 76th Round *Survey of Persons with Disabilities* is administered by India's Ministry of Statistics and Programme Implementation. Authorised users may obtain the survey microdata, metadata, questionnaire, and technical documentation through the official [NSS-76 catalogue](https://microdata.gov.in/NADA/index.php/catalog/154), subject to its data-access agreement.

## Reproducing the analysis

Once analysis files are added, the intended workflow is:

1. Obtain authorised NSS-76 microdata directly from the official source.
2. Place the locally authorised files in `data/raw/` (this directory is ignored by Git).
3. Run the scripts in `code/` in numerical order.
4. Compare regenerated outputs with the aggregate tables and figures in `derived_aggregates/` and `output/`.

The repository will contain only material that can be made public safely.

## Repository structure

- `code/` — analysis scripts and environment instructions
- `data_dictionary/` — variable definitions and construction rules
- `derived_aggregates/` — public aggregate estimates only
- `output/` — regenerated tables and figures
- `docs/` — reproducibility and data-access documentation

## Citation

If you use these materials, please cite the accompanying manuscript. A release-specific Zenodo DOI will be added after the first archived GitHub release.

## License

Unless otherwise stated, code in this repository is released under the [MIT License](LICENSE). No licence is granted for NSS-76 microdata or other restricted source files.
