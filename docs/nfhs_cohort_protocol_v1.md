# Frozen NFHS-5 Bihar cohort and outcome-definition protocol

**Protocol ID:** `BIM-NFHS5-COHORT-OUTCOME-v1.0.0`  
**Frozen:** 2026-11-02, before access to individual NFHS-5 Births Recode data.  
**Status:** design freeze, **not** a completed analysis or prospective registration.

## Purpose and boundaries

Primary objective is to estimate and predict the risk of death before age one among Bihar births using ethically authorized NFHS-5 BR data. Secondary aims are age-specific outcomes and calibration/transportability. The historical 2010–12 AHS 37-district ecological analysis is a **separate study** and may never be joined to individual NFHS-5 births as contemporaneous predictors.

The following are explicitly distinct: (A) conditional **birth-cohort prediction**, (B) right-censored **survival modelling**, (C) **official DHS synthetic-cohort period mortality estimates**. The outcome number from (A) is NOT Bihar's official NFHS-5 IMR. Each has a different denominator and estimand.

## Frozen cohorts

| Track | Entry | Follow-up | Infant death target | Censoring |
|---|---|---|---|---|
| A. Complete-follow-up binary classification | Bihar births with CMC `v008-b3` in 13–59 inclusive | Full 12 months conservatively assured | `b5=0, b7=0..11` | None needed; invalid death ages excluded/audited |
| B. Discrete-time infant survival | Bihar births with CMC difference 0–59 | Monthly age intervals 0..11 | Died in 0..11 completed months | Alive: last **guaranteed** age-month `max(0, v008-b3-1)` capped at 12; died at/after month 12: administratively at 12 |
| C. Official period IMR reproduction | DHS reference-period and age segment risk sets | Period-specific, synthetic cohort | DHS stage-specific mortality probabilities | DHS design-based estimation; independent from A and B |

*Why minus one for alive censoring?* CMC gives calendar **months**, not interview/birth dates. Subtracting one is deliberately conservative about guaranteed completed follow-up; this is a sensitivity choice, **not the DHS standard mortality-rate algorithm**. Births with zero guaranteed complete months contribute no person-months and are recorded in audit.

*Why 13–59 months for track A?* CMC month difference of 12 may correspond to less than 12 actual elapsed months. Starting at 13 reduces mislabeling living infants as complete one-year survivors. The binary baseline is approximately a 4-year cohort of births and is not the NFHS five-year rate.

## Age-at-death definitions

`b5` is alive (1)/dead (0); `b7` is age at death in completed months, and **may include DHS-imputed age-at-death values**. `b6` retains reporting units: `1dd` days, `2mm` months, `3yy` years, and special codes. The neonatal outcome uses `b6` to identify day-coded deaths:

- Early neonatal: reported death on days 0–2, `b6=100..102`.
- Later neonatal: days 3–27, `b6=103..127`.
- Postneonatal: days 28+ or reported death in completed months 1–11; do not infer exact day from reported month.
- `b7=0` without a valid day-coded `b6` is **unknown neonatal status**, not automatically a neonatal death. A month-zero report, special `b6` code, or contradictory units must be audited.
- A living child needs at least two CMC calendar-month differences to be conservatively classifiable as surviving through 28 days, otherwise neonatal status is censored/unknown.
- Stage-specific survival analyses at exact day resolution are **not approved by this protocol** until age precision and interview/birth day information are verified against data.

Note: `b7<12` is the **infant death** proxy in track A; the day-0–27 category is not interchangeable with age in month zero. Neonatal coding sensitivity and heaping around 28–31 days/one month must be reported.

## Data provenance and identity audit

Read **approved** IIPS NFHS-5 BR on this laptop only. Inspect exact NFHS-5 state value labels; require numeric Bihar code to be confirmed rather than guessing. Essential fields: `v024,v008,b3,b5,b7,b6,v005,v021,b4,b0,bord,b11,v011`. Retain `v001,v002,v003,bidx,caseid` if present to verify uniqueness/grouping, `v022/v023` to verify stratification. A child is uniquely identified by mother's `caseid` plus `bidx` (or verified `v001,v002,v003,bidx`); household by verified `v001,v002`. Missing IDs block claims about household-group leakage checks. Survey state reflects interviewed residence, potentially not birth residence (migration caveat).

Before modelling, produce an exclusion flow with counts and weighted/unweighted death rates at each stage: Bihar births, recent-window births, missing/dead/invalid age, temporal inconsistencies, invalid weights/PSUs, duplicate birth IDs, first-birth structural `b11` missingness, `b6` unavailable or special codes, and zero-exposure survival rows. Keep separate missingness audits among survivors and deceased.

## Predictor availability — locked boundaries

**At-birth baseline only:** sex (`b4`), multiple-birth code (`b0`), birth order (`bord`), preceding birth interval (`b11`, structurally NA for first birth), maternal age at birth using `(b3-v011)/12`. Do not include `b3,b5,b6,b7,v008` raw as predictors. Survey weights/PSUs/strata are design and splitting fields, not predictors.

Potential delivery features (e.g., delivery setting and recorded birth weight) require **separate preregistered feature-set amendment** after actual variable-code verification; birth weight may be missing nonrandomly. Postnatal visits, vaccination, months breastfeeding, last-year household conditions and future outcomes cannot enter an antenatal/at-birth model without establishing temporal availability. `v106` and `v190` measured at interview cannot automatically be treated as past-time predictors.

## Model and evaluation freeze

Primary modelling split **PSU-held-out** (both births of any mother/household automatically stay together). Train/validation/test isolation is mandatory, with preprocessing/imputation fit **on training only**. Never resample across folds. Keep test outcomes untouched until all model selection and calibration are locked. Suggested baselines: intercept-only prevalence, logistic regression, Random Forest, histogram gradient boosting; other models are exploratory amendments.

Primary metrics: PR-AUC, ROC-AUC, weighted Brier score, calibration intercept and slope, calibration curves and interval uncertainty. Include absolute risk, event prevalence, sensitivity, specificity, PPV, false alarms per true event and decision-threshold dependence. Weighted predictions are *not* enough to claim full survey-design inference: account for normalized `v005`, sampling PSU `v021`, verified `v022/v023` stratum, and suitable design variance/cluster-bootstrap methods. Some clusters may be sparse for district or equity subgroups: suppress or label unreliable estimates.

Cross-round NFHS-4→NFHS-5 and district-held-out generalization are **conditional** on permitted data, harmonized geography, outcome definitions and enough events. Group-held-out CV in 37+ districts is not assured feasible solely because district labels exist.

## Non-negotiable gates and amendments

1. **Access gate:** authorized individual NFHS-5 BR received; until then no training/inference on actual individual children.
2. **Schema gate:** confirm Indian NFHS-5 value labels, identifier/strata variables, and `b6` age codes; document data dictionary.
3. **Timing gate:** fail use of any feature unavailable at the chosen timepoint.
4. **Design gate:** separate predictive metrics from correctly estimated state period rates.
5. **Validation gate:** no duplicate births or PSU/mother/household cross-fold overlap.
6. **Freeze gate:** record protocol SHA-256 in the lock manifest. Any change must be logged with version, rationale and whether outcomes were already examined.

No causal interpretation of SHAP or associations; no clinical triage use; no redistribution of restricted data.

## Primary documentation

- DHS Guide to DHS Statistics, infant and child mortality: https://preview.dhsprogram.com/pubs/pdf/DHSG1/Guide_to_DHS_Statistics_DHS-7_v2.pdf
- DHS VI Recode Manual (b3/b5/b6/b7 and identity/design fields): https://www.dhsprogram.com/pubs/pdf/DHSG4/Recode6_DHS_22March2013_DHSG4.pdf
- DHS.rates paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC6534308/
- Authorized IIPS NFHS data request: https://www.nfhsiips.in/nfhsuser/datarequest.php
- Comparison literature: `results/literature_core5/core_five_comparison_report.md`
