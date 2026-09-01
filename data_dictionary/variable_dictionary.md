# Variable Dictionary

All source fields below refer to the official NSS-76 public-use files. The repository deliberately excludes every unit-level source file.

| Analytic variable | Source file and field(s) | Construction | Use |
| --- | --- | --- | --- |
| `HHID` | All linked files: `HHID` | Official household identifier. | Linkage. |
| `person_serial` | Level 6 and Level 13: `Srl_col1block_5`; Level 2: `Person_Srl_No` | Renamed to a common person-identifier field and linked with `HHID`. | Linkage. |
| `age_person` | Block 3 / Level 2: `Age` | Age in years. The analysis retains records where this equals the Level-6 disability-record age. | Eligibility and age stages. |
| `age_visual` | Block 5.2 / Level 6: `Age_years_col_2_block_5` | Age recorded in the visual-disability module. | Linkage-quality check. |
| `visual_disability_category` | Block 5.2 / Level 6: `Category_of_disability` | Records with codes 1–5 are retained; codes are grouped as no light perception, up to 3 ft, and 3–10 ft for standardisation. | Eligibility and severity adjustment. |
| `support` | Block 7 / Level 13: `Attended_preschool_intervent_pro` | 1 = reported attendance; 2 = no reported attendance. Recoded as 1/0. | Exposure-associated characteristic. |
| `ordinary_school_ever` | Block 7 / Level 13: `Ever_enrolled_ordinary_school` | 1 = yes; 2 = no. Recoded as 1/0. | Main association outcome. |
| `ordinary_school_current` | Block 7 / Level 13: `Currently_attending_ordinary_sch` | 1 = yes; 2 = no. Recoded as 1/0. | Age-stage occupancy outcome. |
| `sex` | Block 3 / Level 2: `Gender` | Codes 1 and 2 retained. | Standardisation. |
| `sector` | Level 6 / Block 1: `Sector` | Rural/urban survey sector. | Standardisation and design. |
| `mpce` | Block 4 / Level 3: `Usual_monthly_consumer_expenditu` | Positive values only; weighted within-population tertiles are recalculated for every analysis population. | Standardisation. |
| `MULT` | Block 5.2 / Level 6: `MULT` | Official final multiplier. | All survey-weighted estimates. |
| `design_stratum` | Block 1 / Level 6: `StateCode`, `Sector`, `Stratum`, `Sub_stratum` | Concatenated design-stratum identifier. | PSU bootstrap. |
| `psu` | Block 1 / Level 6: `FSU_Serial_No` plus design-stratum fields | Concatenated PSU identifier nested within stratum. | PSU bootstrap. |

## Interpretation restriction

`support` is a recorded survey characteristic. It does not identify intervention timing, duration, provider, quality, or causal effect. Every reported support contrast is therefore an adjusted association, not an effect estimate.
