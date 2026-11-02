"""Synthetic-only checks; the NFHS-5 restricted Births Recode is NOT supplied."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.nfhs_cohort_v1 import build_cohorts,PROTOCOL_ID


def synth():
    lags=[0,1,2,13,20,20,20,20,20,20,12,20,20,20]
    birth=[1,1,1,1,0,0,0,0,0,0,1,0,0,1]
    b7=[np.nan,np.nan,np.nan,np.nan,0,0,1,0,3,14,np.nan,15,np.nan,np.nan]
    b6=[np.nan,np.nan,np.nan,np.nan,100,104,130,200,203,214,np.nan,115,100,np.nan]
    v005=[1e6]*14
    v005[13]=0
    return pd.DataFrame({
        "caseid":["m"+str(i) for i in range(14)],
        "v024":["Bihar"]*14,"v008":[1450]*14,
        "b3":[1450-n for n in lags],"b5":birth,"b7":b7,"b6":b6,
        "v005":v005,"v021":[1+i//4 for i in range(14)],
        "v001":[1+i//4 for i in range(14)],
        "v002":[1+i for i in range(14)],
        "v003":[1]*14,"bidx":[1]*14,
        "b4":[1,2]*7,"b0":[0]*14,"bord":[1,2]*7,
        "b11":[np.nan,24]*7,"v011":[1100]*14,
        "v022":[2]*14,
    })


def test_cohort_eligibility_and_censoring():
    binary,survival,person,audit=build_cohorts(synth())
    assert audit["protocol_id"]==PROTOCOL_ID
    assert len(survival)==11  # invalid b6/b7 conflict, missing death month, weight
    assert len(binary)==7
    assert audit["invalid_or_inconsistent_death_month"]==1
    assert audit["clearly_inconsistent_b6_b7_units"]==1
    assert audit["invalid_weight_or_psu"]==1
    row=survival.set_index("birth_record_id")
    assert row.loc["m0|1","survival_observed_months"]==0
    assert row.loc["m1|1","survival_observed_months"]==0
    assert row.loc["m2|1","survival_observed_months"]==1
    assert row.loc["m3|1","survival_observed_months"]==12
    assert row.loc["m4|1","survival_observed_months"]==1
    assert row.loc["m9|1","survival_observed_months"]==12
    assert audit["person_month_events"]==audit["survival_events_infant_under12"]
    assert person.age_month_interval.between(0,11).all()
    assert not binary.cmc_month_difference.lt(13).any()


def test_exact_day_neonatal_vs_month_zero_ambiguity():
    _,s,_,_=build_cohorts(synth())
    s=s.set_index("birth_record_id")
    assert s.loc["m4|1","neonatal_death_0_27_days"]==1
    assert s.loc["m5|1","neonatal_death_0_27_days"]==1
    assert s.loc["m6|1","neonatal_death_0_27_days"]==0
    assert pd.isna(s.loc["m7|1","neonatal_death_0_27_days"])
    assert s.loc["m8|1","neonatal_death_0_27_days"]==0
    assert pd.isna(s.loc["m1|1","neonatal_death_0_27_days"])
    assert s.loc["m2|1","neonatal_death_0_27_days"]==0
    assert s.loc["m5|1","death_age_stage_or_status"]=="death_days_3_27"
    assert s.loc["m6|1","death_age_stage_or_status"]=="death_days_28_31"


def test_monthly_person_period_has_exactly_one_event_per_infant_death():
    _,s,person,_=build_cohorts(synth())
    for _,r in s.iterrows():
        rows=person[person.birth_record_id.eq(r.birth_record_id)]
        assert len(rows)==r.survival_observed_months
        assert rows.infant_death_this_interval.sum()==r.infant_death
        if r.infant_death:
            assert rows.iloc[-1].infant_death_this_interval==1


def test_reject_unknown_numeric_bihar_code():
    sample=synth()
    sample["v024"]=7
    with pytest.raises(ValueError,match="Numeric v024"):
        build_cohorts(sample)
    _,s,_,_=build_cohorts(sample,state_code=7)
    assert len(s)==11


def test_no_birth_duplicates_or_missing_family_identity():
    sample=synth()
    sample.loc[4,"caseid"]="m3"
    with pytest.raises(ValueError,match="Duplicate birth identities"):
        build_cohorts(sample)
    sample=synth().drop(columns=["caseid","v003"])
    with pytest.raises(ValueError,match="caseid or v003"):
        build_cohorts(sample)


def test_reject_missing_b6_field_for_neonatal_protocol():
    with pytest.raises(ValueError,match="b6"):
        build_cohorts(synth().drop(columns="b6"))


def test_protocol_frozen_policy_and_no_forbidden_birthtime_features():
    root=Path(__file__).resolve().parents[1]
    policy=json.loads((root/"docs/nfhs_cohort_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["protocol_id"]==PROTOCOL_ID
    assert policy["protocol_status"]=="FROZEN_BEFORE_AUTHORIZED_MICRODATA"
    assert not set(["b5","b6","b7","v008"]).intersection(
        ["child_sex","multiple_birth","birth_order",
         "preceding_interval_months","maternal_age_birth_years"])
