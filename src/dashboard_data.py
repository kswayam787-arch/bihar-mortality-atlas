"""Read-only verified datasets for Bihar Infant Mortality dashboard.

Strictly descriptive/ecological. No patient-level prediction, synthetic IMR
or invented cross-survey mortality risk estimate.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import pandas as pd
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parents[1]
AHS=ROOT/"data/public/official/derived"
NFHS=ROOT/"results/nfhs5_district"
STUDY=ROOT/"results/ahs_historical_study"
PAPERS=ROOT/"results/literature_core5"
ROUNDS=("2010-11","2011-12","2012-13")
COLORS={"2010-11":"#f3ad73","2011-12":"#45ddbb","2012-13":"#77a6ff"}
AHS_VARIABLES={
    "Institutional deliveries":"institutional_delivery_pct",
    "Early antenatal care":"anc_first_trimester_pct",
    "Three or more ANC visits":"anc_3plus_pct",
    "Birth weight recorded":"birth_weight_measured_pct",
    "Newborn check within 24h":"newborn_check_24h_pct",
    "Maternal postnatal check within 48h":"mother_postnatal_48h_pct",
    "Low birth weight among measured":"low_birth_weight_among_measured_pct",
    "Breastfed within first hour":"breastfed_first_hour_pct",
}


def _load_csv(path, required, min_rows):
    if not path.is_file():raise FileNotFoundError(f"Published/derived source missing: {path}")
    df=pd.read_csv(path)
    missing=set(required)-set(df.columns)
    if missing:raise ValueError(f"Unexpected schema {path.name}; missing {sorted(missing)}")
    if len(df)<min_rows:raise ValueError(f"Unexpectedly small data source {path.name}: {len(df)}")
    return df


def load_public_data():
    state=_load_csv(AHS/"ahs_bihar_state_imr_2010_2013.csv",
                    ["round","imr_per_1000_live_births"],3)
    historical=_load_csv(AHS/"ahs_bihar_district_imr_2010_2013.csv",
                         ["district_source_name","round","imr_per_1000_live_births"],111)
    panel=_load_csv(AHS/"ahs_bihar_mortality_health_panel_2010_2012.csv",
                    ["District","survey_round","infant_imr"]+list(AHS_VARIABLES.values()),74)
    nfhs=_load_csv(NFHS/"bihar_district_selected_indicators.csv",
                   ["District","Four or more ANC visits","Institutional births",
                    "Child stunting under 5"],38)
    summary=_load_csv(NFHS/"indicator_summary.csv",
                      ["indicator","equal_district_mean_percent"],19)
    papers=_load_csv(PAPERS/"papers.csv",
                    ["title","year","doi","study_design_and_denominators",
                     "outcome","main_reported_results","limitations"],5)
    correl=_load_csv(STUDY/"per_round_correlations.csv",
                     ["survey_round","feature","spearman_rho","fdr_bh_p"],14)
    if historical["district_source_name"].nunique()!=37 or len(historical)!=111:
        raise ValueError("AHS 37-district, 3-round geographic audit mismatch")
    if panel["District"].nunique()!=37 or panel.duplicated(["District","survey_round"]).any():
        raise ValueError("AHS matched health-outcome join invalid")
    if nfhs["District"].nunique()!=38:
        raise ValueError("NFHS-5 38-district fact sheet source mismatch")
    if set(state["round"])!=set(ROUNDS):
        raise ValueError("Missing AHS historical statewide rounds")
    if len(papers)!=5:raise ValueError("Literature register should hold five core papers")
    return {"state":state,"historical":historical,"panel":panel,
            "nfhs":nfhs,"summary":summary,"papers":papers,"correl":correl}


def ahs_rounded_rate(data,round_):
    x=data["state"].set_index("round")
    return float(x.loc[round_,"imr_per_1000_live_births"])


def historical_round(data,round_):
    if round_ not in ROUNDS:raise ValueError(f"Unexpected AHS round: {round_}")
    sub=data["historical"].loc[
        data["historical"]["round"].eq(round_),
        ["district_source_name","imr_per_1000_live_births",
         "male_imr_per_1000_live_births","female_imr_per_1000_live_births"]].copy()
    return sub.rename(columns={"district_source_name":"District",
                               "imr_per_1000_live_births":"IMR"}).sort_values("IMR",ascending=False)


def nfhs_sorted(data,indicator,ascending=False):
    if indicator not in data["nfhs"] or indicator=="District":
        raise ValueError("Unknown NFHS-5 public indicator")
    df=data["nfhs"][["District",indicator]].dropna().copy()
    return df.sort_values(indicator,ascending=ascending)


def ecology(data,round_,feature):
    if round_ not in ("2010-11","2011-12"):raise ValueError("AHS matched care years 2010-11 and 2011-12 only")
    if feature not in AHS_VARIABLES.values():raise ValueError("Unknown AHS healthcare feature")
    df=data["panel"].loc[
        data["panel"].survey_round.eq(round_),
        ["District","infant_imr",feature]].dropna().copy()
    rho,p=spearmanr(df[feature],df["infant_imr"])
    row=data["correl"].loc[
        data["correl"].survey_round.eq(round_) &
        data["correl"].feature.eq(feature)]
    fdr=float(row["fdr_bh_p"].iloc[0]) if len(row)==1 else None
    return df, float(rho),float(p),fdr


def readiness():
    lock=ROOT/"docs/nfhs_protocol_lock_v1.json"
    if lock.is_file():
        meta=json.loads(lock.read_text(encoding="utf-8"))
        checks=meta.get("source_file_sha256",{})
        integrity=all((ROOT/path).is_file() and
                      hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
                      for path,digest in checks.items())
        integrity=bool(checks) and integrity
    else:
        meta={}
        integrity=False
    raw=ROOT/"data/raw"
    # Presence is only a signal, not automatic confirmation of IIPS access.
    rawfiles=[p.name for p in raw.iterdir() if p.is_file() and p.suffix.lower() in (".dta",".sav",".csv")] if raw.exists() else []
    return {"protocol_id":meta.get("protocol_id","Not verified"),
            "protocol_lock_valid":integrity,
            "authorized_microdata_confirmed":False,
            "raw_candidates_count":len(rawfiles),
            "historical_ahs_ready":(AHS/"ahs_bihar_district_imr_2010_2013.csv").exists(),
            "nfhs_district_indicators_ready":(NFHS/"bihar_district_selected_indicators.csv").exists(),
            "literature_ready":(PAPERS/"papers.csv").exists()}
