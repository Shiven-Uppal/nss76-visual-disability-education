# Reproducibility and Data-Access Statement

## Scope

This repository supports the analysis reported in *Early Educational Support and Ordinary-School Participation among Persons with Visual Disability in India: NSS-76 Evidence and a Partially Identified Age-Stage Markov Framework*.

## Restricted source data

The analysis uses unit-level records from the NSS 76th Round *Survey of Persons with Disabilities*. These source data are not included in this repository and must not be uploaded, redistributed, or committed to version control.

Researchers seeking to reproduce the analysis must obtain authorised access independently from the official NSS Online Microdata Library: https://microdata.gov.in/NADA/index.php/catalog/154

## Public materials

This repository is intended to provide:

- complete analysis specifications;
- code to prepare analytic variables and estimates from authorised data;
- a public variable dictionary;
- derived aggregate estimates that do not disclose unit-level records;
- figure and table-generation code; and
- software-environment information.

## Planned verification workflow

1. Obtain authorised NSS-76 data and retain them only in a local, access-controlled location.
2. Configure the local data path without storing it in version control.
3. Run the cleaning and analytic scripts in their stated order.
4. Compare the regenerated estimates with the public aggregate outputs.
5. Report any discrepancy with the repository version and operating environment.

## Archiving

A versioned GitHub release will be archived through Zenodo before manuscript submission. The resulting DOI will be added to the manuscript's data-availability statement and to this repository.
