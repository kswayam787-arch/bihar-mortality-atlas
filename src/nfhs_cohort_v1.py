"""Frozen protocol v1: audited NFHS-5 Bihar birth cohorts and monthly person-time.

Not the official DHS synthetic-cohort estimator. No NFHS records are bundled.
See docs/nfhs_cohort_protocol_v1.md and docs/nfhs_cohort_policy_v1.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

PROTOCOL_ID="BIM-NFHS5-COHORT-OUTCOME-v1.0.0"
CORE={"v024","v008","b3","b5","b7","b6","v005","v021",
      "b4","b0","bord","b11","v011","v001","v002","bidx"}
OPTIONAL={"caseid","v003","v022","v023","v025","v106","v190"}
PREDICTORS=("child_sex","multiple_birth","birth_order",
            "preceding_interval_months","maternal_age_birth_years")


def selected_bihar(raw:pd.DataFrame,bihar_mask=None,state_code=None):
    if bihar_mask is not None:
        mask=pd.Series(bihar_mask,index=raw.index).fillna(False).astype(bool)
        if not mask.any():raise ValueError("Bihar mask selects no births")
        return mask
    if state_code is not None:
        mask=raw["v024"].astype("string").str.strip().eq(str(state_code))
    else:
        if pd.api.types.is_numeric_dtype(raw["v024"]):
            raise ValueError("Numeric v024 cannot be inferred: verify Bihar state code and supply state_code")
        mask=raw["v024"].astype("string").str.strip().str.casefold().eq("bihar")
    if not mask.fillna(False).any():
        raise ValueError("No Bihar rows; inspect NFHS-5 state labels and state_code")
    return mask.fillna(False).astype(bool)


def load_approved_br(path:Path):
    """Read only permitted user-supplied BR; do not fetch or guess protected data."""
    if path.suffix.lower()==".csv":
        return pd.read_csv(path,low_memory=False)
    if path.suffix.lower()==".dta":
        with pd.io.stata.StataReader(str(path),convert_categoricals=False) as reader:
            names=set(reader.variable_labels())
            cols=sorted((CORE|OPTIONAL)&names)
            raw=reader.read(columns=cols)
        # State value-label decoding still needs real data codebook inspection.
        return raw
    raise ValueError("Pass approved .csv or .dta Births Recode")


def make_ids(df:pd.DataFrame):
    # Explicit household and child identity needed for duplicate and leakage checks.
    if not {"v001","v002","bidx"}.issubset(df):
        raise ValueError("Missing cluster/household/birth identifiers")
    if "caseid" in df:
        mother=df["caseid"].astype("string").str.strip()
        if mother.isna().any() or mother.eq("").any():
            raise ValueError("Empty or unknown caseid: identity audit blocked")
    elif "v003" in df:
        if df["v003"].isna().any():
            raise ValueError("Missing v003 for mother identifier")
        mother=(df["v001"].astype("string").str.strip()+"|"+
                df["v002"].astype("string").str.strip()+"|"+
                df["v003"].astype("string").str.strip())
    else:
        raise ValueError("Missing caseid AND v003: cannot group repeated births by mother")
    if df[["v001","v002","bidx"]].isna().any().any():
        raise ValueError("Missing v001, v002, or bidx identity field")
    household=(df["v001"].astype("string").str.strip()+"|"+
               df["v002"].astype("string").str.strip())
    birthid=mother+"|"+df["bidx"].astype("string").str.strip()
    if birthid.duplicated().any():
        raise ValueError("Duplicate birth identities: caseid/bidx cannot be used safely")
    return mother,household,birthid


def neonatal_class(b5,b7,b6,cmc_lag):
    """Return 0/1/None for death in days 0-27, and a granular death stage."""
    if b5==1:
        return (0,"survived_neonatal") if cmc_lag>=2 else (None,"neonatal_followup_incomplete")
    if not np.isfinite(b7):
        return None,"unknown_death_age"
    if not np.isfinite(b6) or b6!=int(b6):
        return None,"b6_missing_or_noninteger"
    b6=int(b6)
    if 100<=b6<=131:
        day=b6-100
        if day<=27 and b7==0:
            return (1,"death_days_0_2") if day<=2 else (1,"death_days_3_27")
        if 28<=day<=31 and b7 in (0,1):
            return 0,"death_days_28_31"
        return None,"inconsistent_day_code_and_completed_months"
    if 201<=b6<=289 and b7>=1:
        if b7<12:return 0,"death_months_1_11"
        return 0,"death_age_12plus_months"
    if 301<=b6<=389 and b7>=12:
        return 0,"death_age_12plus_months"
    return None,"neonatal_age_ambiguous"


def build_cohorts(raw:pd.DataFrame,bihar_mask=None,state_code=None):
    """Return (complete_followup, survival_births, monthly_person_time, audit).

    Binary age 13..59 CMC differences; survival age 0..59.
    Living child follow-up is conservative guaranteed completed CMC months.
    """
    missing=CORE-set(raw.columns)
    if missing:
        raise ValueError("Missing NFHS Births Recode fields: "+", ".join(sorted(missing)))
    if not ("caseid" in raw.columns or "v003" in raw.columns):
        raise ValueError("Need caseid or v003 for mother grouping")

    state=selected_bihar(raw,bihar_mask,state_code)
    d=raw.loc[state].copy()
    audit={"protocol_id":PROTOCOL_ID,"source_rows":int(len(raw)),
           "bihar_births":int(len(d))}
    # Identifiers must be valid before dropping records to expose problems.
    mother,house,birth=make_ids(d)
    d["mother_group"]=mother
    d["household_group"]=house
    d["birth_record_id"]=birth

    numeric=["v008","b3","b5","b7","b6","v005","v021",
             "b4","b0","bord","b11","v011","v001","v002","bidx"]
    for name in numeric:
        d[name]=pd.to_numeric(d[name],errors="coerce")
    d["cmc_month_difference"]=d["v008"]-d["b3"]
    in_window=d["cmc_month_difference"].between(0,59)
    audit["excluded_not_births_0_to_59_cmc"]=int((~in_window).sum())
    d=d.loc[in_window].copy()
    audit["births_in_survival_0_to_59_cmc"]=int(len(d))

    status=d["b5"].isin([0,1])
    age_ok=(d["b5"].eq(1) | (
        d["b7"].notna() & d["b7"].ge(0) & d["b7"].le(1199) &
        d["b7"].eq(np.floor(d["b7"])) &
        d["b7"].le(d["cmc_month_difference"])))
    survey_ok=d["v005"].gt(0) & d["v021"].notna()
    stage_unit_conflict=(d["b5"].eq(0) &
         d["b7"].notna() & d["b6"].notna() &
         (((d["b6"].between(100,129)) & d["b7"].ne(0)) |
          ((d["b6"].between(130,131)) & ~d["b7"].isin([0,1])) |
          ((d["b6"].between(301,389)) & d["b7"].lt(12))))
    audit["invalid_b5_status"]=int((~status).sum())
    audit["invalid_or_inconsistent_death_month"]=int((~age_ok).sum())
    audit["invalid_weight_or_psu"]=int((~survey_ok).sum())
    audit["clearly_inconsistent_b6_b7_units"]=int(stage_unit_conflict.sum())
    d=d.loc[status & age_ok & survey_ok & ~stage_unit_conflict].copy()
    d["survey_weight"]=d["v005"]/1_000_000
    d["child_sex"]=d["b4"].where(d["b4"].isin([1,2]))
    d["multiple_birth"]=np.where(d["b0"].isna(),np.nan,
                                 (d["b0"]>0).astype(float))
    d["birth_order"]=d["bord"].where(d["bord"].between(1,30))
    d["preceding_interval_months"]=d["b11"].where(d["b11"].between(1,239))
    d["maternal_age_birth_years"]=(d["b3"]-d["v011"])/12
    d.loc[~d["maternal_age_birth_years"].between(10,54),
          "maternal_age_birth_years"]=np.nan

    stages=[neonatal_class(*v) for v in d[["b5","b7","b6","cmc_month_difference"]].itertuples(index=False,name=None)]
    d["neonatal_death_0_27_days"]=pd.array([x[0] for x in stages],dtype="Int64")
    d["death_age_stage_or_status"]=[x[1] for x in stages]
    audit["neonatal_age_or_followup_unresolved"]=int(d["neonatal_death_0_27_days"].isna().sum())
    audit["reported_b6_absent_among_dead"]=int((d["b5"].eq(0)&d["b6"].isna()).sum())

    d["infant_death"]=((d["b5"]==0)&d["b7"].lt(12)).astype(int)
    d["survival_observed_months"]=np.where(
        d["b5"].eq(0),
        np.where(d["b7"].lt(12),d["b7"]+1,12),
        np.clip(d["cmc_month_difference"]-1,0,12),
    ).astype(int)
    audit["survival_rows_passing_quality_checks"]=int(len(d))
    audit["survival_events_infant_under12"]=int(d["infant_death"].sum())
    audit["zero_complete_month_alive_censors"]=int(((d["b5"]==1)&
                  d["survival_observed_months"].eq(0)).sum())

    fixed_cols=["birth_record_id","mother_group","household_group","v021",
                "survey_weight","cmc_month_difference","survival_observed_months",
                "infant_death","neonatal_death_0_27_days",
                "death_age_stage_or_status"]+list(PREDICTORS)
    survival=d[fixed_cols].rename(columns={"v021":"psu"}).copy()
    binary=survival.loc[survival["cmc_month_difference"].between(13,59)].copy()
    audit["binary_births_13_to_59"]=int(len(binary))
    audit["binary_infant_deaths"]=int(binary["infant_death"].sum())
    audit["binary_weighted_cohort_death_fraction"]=(
        float(np.average(binary["infant_death"],weights=binary["survey_weight"]))
        if len(binary) else None)
    audit["strata_fields_available"]=[s for s in ("v022","v023") if s in d]
    audit["formal_survey_variance_ready"]=False
    audit["formal_survey_variance_blocker"]="Verify NFHS-5-specific strata and variance design; not implemented"
    audit["warning"]="Binary and discrete-time datasets are NOT official DHS period IMR estimates"

    # Every row represents one whole age-month at risk. Event is in final
    # month for deaths before the first birthday, never among censored births.
    person_rows=[]
    for row in survival.itertuples(index=False):
        for month in range(row.survival_observed_months):
            person_rows.append({
                "birth_record_id":row.birth_record_id,
                "mother_group":row.mother_group,
                "household_group":row.household_group,
                "psu":row.psu,
                "survey_weight":row.survey_weight,
                "age_month_interval":month,
                "infant_death_this_interval":int(row.infant_death==1 and month==row.survival_observed_months-1)
            })
    person=pd.DataFrame(person_rows,columns=[
        "birth_record_id","mother_group","household_group","psu","survey_weight",
        "age_month_interval","infant_death_this_interval"])
    audit["person_month_rows"]=int(len(person))
    audit["person_month_events"]=int(person["infant_death_this_interval"].sum())
    assert audit["person_month_events"]==audit["survival_events_infant_under12"]
    assert all(person["age_month_interval"].between(0,11))
    return binary,survival,person,audit


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True,
                    help="Approved NFHS-5 Births Recode .dta or .csv ONLY")
    ap.add_argument("--output-dir",type=Path,
                    default=Path("data/processed/nfhs_protocol_v1"))
    ap.add_argument("--state-code",default=None,
                    help="Verify numeric v024 Bihar value via codebook before use")
    a=ap.parse_args()
    raw=load_approved_br(a.input)
    binary,survival,person,audit=build_cohorts(raw,state_code=a.state_code)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for name,frame in [("binary_complete_followup",binary),
                       ("survival_birth_records",survival),
                       ("survival_person_months",person)]:
        frame.to_parquet(a.output_dir/(name+".parquet"),index=False)
    (a.output_dir/"cohort_audit.json").write_text(
        json.dumps(audit,indent=2),encoding="utf-8")
    print(json.dumps(audit,indent=2))


if __name__=="__main__":
    main()
