"""Bihar Mortality Atlas — published-data research interface.

Run: streamlit run bihar_research_dashboard.py
All public data are historical or ecological; no individual risk prediction.
"""
from __future__ import annotations

import html
from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_data import (
    ROOT, ROUNDS, COLORS, AHS_VARIABLES, load_public_data, ahs_rounded_rate,
    historical_round, nfhs_sorted, ecology, readiness
)

st.set_page_config(
    page_title="BIHAR / Mortality Atlas",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About":"An independently developed, open-data research dashboard. Historical observations, not clinical prediction.",
    }
)

INK="#071421"
PANEL="#101f30"
PANEL2="#15283a"
MUTED="#98aabb"
TEXT="#eaf4f5"
MINT="#60ead0"
ORANGE="#ffb27a"
BLUE="#80a8ff"

CSS=r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {--mint:#60ead0;--page:#071421;--panel:#102133;--muted:#91a7b9;--ink:#eaf4f5}
html, body, [class*="css"], [data-testid="stApp"] {
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
}
.stApp, [data-testid="stAppViewContainer"]{
    background:
    radial-gradient(ellipse at 73% 2%,rgba(46,123,134,.16),transparent 34%),
    radial-gradient(ellipse at 12% 18%,rgba(60,85,161,.13),transparent 31%),
    #071421;
    color:var(--ink)
}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{
  background:#091724; border-right:1px solid rgba(154,193,204,.12)
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#b4c4d0}
.block-container {padding-top:2rem; padding-bottom:4rem;max-width:1420px}
h1,h2,h3{font-family:'Space Grotesk','Segoe UI',sans-serif!important;letter-spacing:-.035em}
h1{font-weight:700!important}
h2{font-size:1.55rem!important;margin-top:.55rem!important}
h3{font-size:1.1rem!important}
p,li {line-height:1.55}
a{color:#6ee5d1!important}
[data-testid="stVerticalBlock"]{gap:.85rem}
[data-testid="stMetric"]{padding:8px}
[data-testid="stMetricValue"]{font-family:'Space Grotesk', sans-serif!important;color:#eaf4f5!important}
[data-testid="stRadio"] [role="radiogroup"]{gap:.45rem}
[data-testid="stRadio"] label{
    border-radius:11px; padding:9px 10px; border:1px solid transparent;
    transition:.15s;
}
[data-testid="stRadio"] label:has(input:checked){background:#193849;border-color:#315f68}
[data-testid="stRadio"] label:hover{background:#152a3c}
[data-baseweb="select"] > div, .stTextInput input{
    background:#132538!important;border:1px solid #2e4457!important;
    border-radius:10px!important;color:#e8f0f1!important
}
.stButton button, [data-testid="stDownloadButton"] button{
    border-radius:10px;background:#193342;border:1px solid #365969;
    color:#bdf3e8; font-weight:600
}
.stButton button:hover,[data-testid="stDownloadButton"] button:hover{
    border-color:#60ead0;color:#e6fff9
}
[data-testid="stDataFrame"]{border:1px solid rgba(139,177,195,.2);border-radius:13px;overflow:hidden}
[data-testid="stExpander"]{border:1px solid #2a4051;border-radius:12px;background:#102031}
[data-testid="stTabs"] button{font-family:'DM Sans',sans-serif}
[data-testid="stAlert"]{border-radius:12px}
[data-testid="stPlotlyChart"]{border-radius:14px;overflow:hidden}
.panel {background:linear-gradient(145deg,#112638,#0d1b2b);border:1px solid #294255;
 border-radius:17px;padding:23px 23px 19px 23px;margin:0 0 8px 0;min-height:122px}
.card-label {font-size:11px;letter-spacing:.1em;color:#97b6c0;text-transform:uppercase;font-weight:700}
.card-value{font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:35px;line-height:1.25;
 font-weight:700;letter-spacing:-.05em;color:#f2fcf8;margin:10px 0 4px}
.card-sub{font-size:12px;color:#91a4b5;line-height:1.6}
.tag {font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:#8df3da;
 padding:6px 10px;border:1px solid #367467;background:#193e3a;
 border-radius:30px;font-weight:700;display:inline-block;margin-bottom:14px}
.hero{
    border-radius:22px;border:1px solid #34505d;overflow:hidden;
    background:
      radial-gradient(ellipse 75% 120% at 90% 0%,rgba(70,223,197,.17),transparent 58%),
      linear-gradient(120deg,#112a3c,#0a1929 83%);
    padding:36px 38px;margin:10px 0 26px;
    position:relative;
}
.hero h1{font-size:clamp(2.4rem,5vw,4rem)!important;letter-spacing:-.065em;line-height:1.03;
margin:1px 0 17px!important;color:#f4fcfd}
.hero p{max-width:670px;font-size:15px;color:#a8c3cd;margin:0;line-height:1.8}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#7be8d5;font-weight:700}
.hero-meta{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}
.hero-meta span{color:#bad6dc;border:1px solid #3c5a65;background:#162d3c;border-radius:50px;
padding:6px 13px;font-size:12px}
.section-eyebrow{font-size:11px;letter-spacing:.13em;color:#79d8ca;text-transform:uppercase;font-weight:700;margin-bottom:8px}
.section-note{font-size:12px;color:#93a8b9;margin-top:-.25rem;margin-bottom:1rem}
.rule{height:1px;background:linear-gradient(90deg,#4b7276,transparent);margin:24px 0}
.side-logo{font-family:'Space Grotesk',sans-serif;font-size:19px;font-weight:700;letter-spacing:-.04em;color:#eefdfb;
 padding-top:18px}
.side-logo b{color:#6de5cb}
.side-caption{font-size:11px;color:#7795a6;letter-spacing:.1em;text-transform:uppercase;margin:3px 0 24px}
.pill-status{display:inline-block;color:#94dfc9;background:#133e36;
font-size:11px;border:1px solid #356e5c;border-radius:20px;padding:4px 10px}
.lit-card{border-radius:15px;border:1px solid #2b4558;background:#0e2132;
padding:19px 22px;margin:9px 0}
.lit-number{color:#6bd9c7;font-weight:700;font-size:11px;letter-spacing:.1em}
.lit-heading{font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;
color:#f1fafa;margin-top:7px;margin-bottom:10px}
.lit-sub{font-size:12px;color:#9db4c0;line-height:1.7}
.mini-note{background:#132a37;border-left:3px solid #4cdbc1;
padding:12px 16px;color:#b5cbd4;border-radius:7px;font-size:12px;margin:12px 0 18px}
.codebox{background:#07131e;color:#c0eadd;border:1px solid #334e5c;border-radius:12px;
 padding:15px 18px;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap}
.smallfooter{font-size:11px;color:#7994a3;padding:24px 0 0;border-top:1px solid #284154}
@media(max-width:768px){
 .hero{padding:26px 20px;border-radius:17px}
 .hero h1{font-size:2.4rem!important}
 .panel{padding:17px}
 .card-value{font-size:28px}
 .block-container{padding-left:1rem;padding-right:1rem}
}
</style>
"""
st.markdown(CSS,unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def dataset():
    return load_public_data()


def escaped(x):
    return html.escape(str(x),quote=True)


def box_metric(label,value,sub,color=MINT):
    st.markdown(
        f'<div class="panel"><div class="card-label">{escaped(label)}</div>'
        f'<div class="card-value" style="color:{color}">{escaped(value)}</div>'
        f'<div class="card-sub">{escaped(sub)}</div></div>', unsafe_allow_html=True
    )


def section(eyebrow,title,description=""):
    st.markdown(f'<div class="section-eyebrow">{escaped(eyebrow)}</div>',
                unsafe_allow_html=True)
    st.subheader(title)
    if description:
        st.markdown(f'<div class="section-note">{escaped(description)}</div>',
                    unsafe_allow_html=True)


def chart_style(fig,height=440,legend=False):
    fig.update_layout(
        height=height,margin=dict(l=5,r=5,t=38,b=20),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Segoe UI",size=12,color="#b7cbd5"),
        title_font=dict(size=15,color="#effafa"),
        xaxis=dict(gridcolor="rgba(139,174,196,.11)",zeroline=False,linecolor="#3a5363",
                   tickfont=dict(color="#9aafb9")),
        yaxis=dict(gridcolor="rgba(139,174,196,.11)",zeroline=False,linecolor="#3a5363",
                   tickfont=dict(color="#9aafb9")),
        showlegend=legend,
        legend=dict(orientation="h",y=1.1,x=0,font=dict(color="#adbdc8")),
        hoverlabel=dict(bgcolor="#122d3e",font=dict(color="#e5fbfb")),
    )
    return fig


def plot_bar(values,lab,value_col,color=MINT,height=440,xaxis_title=""):
    fig=go.Figure(go.Bar(
        x=values[value_col],y=values[lab],orientation="h",
        marker=dict(color=color,line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}<extra></extra>"
    ))
    fig.update_yaxes(autorange="reversed",title="")
    fig.update_xaxes(title=xaxis_title)
    chart_style(fig,height=height)
    st.plotly_chart(fig,width="stretch",config={"displaylogo":False})


def hero():
    st.markdown("""
      <div class="hero">
       <div class="tag">✳  Population health intelligence / India</div>
       <h1>BIHAR<br>MORTALITY <span style="color:#66e5c9">ATLAS.</span></h1>
       <p>Explore historical infant mortality, maternal-health access, and district disparities
       through verified published datasets and reproducible analysis.</p>
       <div class="hero-meta">
         <span>◈  AHS 2010–2013</span><span>◈  NFHS-5 2019–21</span>
         <span>◈  Research-grade methodology</span>
       </div>
      </div>
    """,unsafe_allow_html=True)


try:
    D=dataset()
except (FileNotFoundError,ValueError) as exc:
    st.error(f"Data integrity check failed: {exc}")
    st.stop()

with st.sidebar:
    st.markdown('<div class="side-logo"><b>✳</b> Mortality Atlas</div>'
                '<div class="side-caption">Bihar / Research Studio</div>',unsafe_allow_html=True)
    menu=["Overview","Historical mortality","Healthcare & districts","Literature library","Research pipeline"]
    page=st.radio("Workspace",menu,label_visibility="collapsed")
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Data status</div>',unsafe_allow_html=True)
    st.markdown('<span class="pill-status">● Public datasets loaded</span>',unsafe_allow_html=True)
    st.caption("No individual-level mortality prediction. All comparisons are observational.")
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.caption("Local research app · V1.0")
    st.caption("Source files stay on your computer.")


if page=="Overview":
    hero()
    section("01 / Intelligence snapshot","The state at a glance",
            "Historical AHS mortality and NFHS-5 published healthcare indicators are different datasets.")
    a,b,c,d=st.columns(4)
    with a:box_metric("AHS Bihar IMR · 2012–13","48","Infant deaths / 1,000 live births")
    with b:box_metric("AHS historical districts","37","Census-era district units",BLUE)
    with c:box_metric("NFHS-5 districts","38","Published 2019–21 indicator coverage",ORANGE)
    with d:box_metric("Verified core papers","05","Primary full-text evidence register")
    st.markdown('<div class="mini-note">AHS mortality figures are from 2010–13; '
                'NFHS-5 district indicators are from 2019–21. '
                'Neither dataset supplies an individual infant risk score.</div>',
                unsafe_allow_html=True)
    left,right=st.columns([1.06,.94],gap="large")
    with left:
        section("Historical signal","Bihar infant mortality trend",
                "Official AHS estimates, deaths under 12 months per 1,000 live births.")
        frame=D["state"].set_index("round").loc[list(ROUNDS)].reset_index()
        fig=go.Figure()
        fig.add_trace(go.Scatter(
            x=frame["round"],y=frame["imr_per_1000_live_births"],
            mode="lines+markers+text",
            text=[str(int(x)) for x in frame["imr_per_1000_live_births"]],
            textposition="top center",
            line=dict(color=MINT,width=4,shape="spline"),
            marker=dict(size=12,color="#071421",line=dict(width=3,color=MINT)),
            textfont=dict(size=15,color="#edfdf8"),
            hovertemplate="AHS %{x}<br>%{y:.0f} deaths/1,000<extra></extra>"
        ))
        fig.update_yaxes(range=[0,68],title="Infant deaths per 1,000")
        fig.update_xaxes(title="")
        chart_style(fig,390)
        st.plotly_chart(fig,width="stretch",config={"displaylogo":False})
    with right:
        section("Geographic variation","Highest historical IMR",
                "Six districts with the highest reported values, AHS 2012–13.")
        ranked=historical_round(D,"2012-13").head(6).sort_values("IMR",ascending=False)
        plot_bar(ranked,"District","IMR",ORANGE,390,"Deaths per 1,000")
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    section("Public-service access","NFHS-5 district indicator overview",
            "These are unweighted means of 38 district percentages, not the Bihar state estimate.")
    highlights=["Four or more ANC visits","Institutional births",
                "Improved sanitation","Anaemia among pregnant women"]
    cols=st.columns(4)
    for col,ind in zip(cols,highlights):
        mean=float(D["nfhs"][ind].mean())
        with col:box_metric(ind,f"{mean:.1f}%","Equal-district average",
                            color=ORANGE if "Anaemia" in ind else MINT)
    st.caption("District means are descriptive. For state-level estimates, use official NFHS weighted estimates and uncertainty.")


elif page=="Historical mortality":
    st.markdown('<div class="eyebrow">02 / Annual health survey</div>',unsafe_allow_html=True)
    st.title("Historical mortality explorer")
    st.write("Explore 37 AHS districts over three rounds. These are historical survey outcomes, not live health data.")
    c1,c2=st.columns([1,2])
    with c1:wave=st.selectbox("AHS round",ROUNDS,index=2)
    with c2:stage=st.selectbox("Mortality outcome",["Infant mortality",
         "Male infant mortality","Female infant mortality"])
    m={"Infant mortality":"IMR",
       "Male infant mortality":"male_imr_per_1000_live_births",
       "Female infant mortality":"female_imr_per_1000_live_births"}[stage]
    ds=historical_round(D,wave)
    primary=ds.sort_values(m,ascending=False)
    k1,k2,k3=st.columns(3)
    with k1:box_metric("Bihar statewide IMR",f"{ahs_rounded_rate(D,wave):.0f}",
                       "Per 1,000 births · statewide (both sexes)")
    with k2:box_metric("Highest district rate",f"{primary[m].max():.0f}",
                       str(primary.iloc[0].District),ORANGE)
    with k3:box_metric("Lowest district rate",f"{primary[m].min():.0f}",
                       str(primary.iloc[-1].District),BLUE)
    section("District distribution","Compare historical districts",
            "Choose a mortality measure; ranked district rates are survey estimates with sampling uncertainty.")
    qty=st.slider("Districts shown",min_value=8,max_value=37,value=18,step=1)
    plot_bar(primary.head(qty),"District",m,ORANGE if "Male" in stage else MINT,
             height=max(380,qty*29),xaxis_title="Deaths per 1,000 live births")
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    section("Individual district history","Track a district over three AHS rounds")
    pick=st.selectbox("Choose a historical AHS district",sorted(ds["District"].unique()))
    hist=D["historical"].loc[
        D["historical"].district_source_name.eq(pick)].copy()
    hist["round"]=pd.Categorical(hist["round"],categories=ROUNDS,ordered=True)
    hist=hist.sort_values("round")
    fig=go.Figure(go.Scatter(
        x=hist["round"].astype(str),y=hist["imr_per_1000_live_births"],
        mode="lines+markers+text",text=hist["imr_per_1000_live_births"],
        textposition="top center",
        line=dict(color=BLUE,width=3),
        marker=dict(size=11,color=BLUE),
        hovertemplate="%{x}: %{y} deaths/1,000<extra></extra>"
    ))
    fig.update_yaxes(title="Infant deaths per 1,000",rangemode="tozero")
    chart_style(fig,320)
    st.plotly_chart(fig,width="stretch",config={"displaylogo":False})
    st.download_button("Export historical district rates (CSV)",
                       D["historical"].to_csv(index=False).encode("utf-8-sig"),
                       "bihar_ahs_historical_imr.csv","text/csv")
    st.info("AHS 2010–13 estimates have different survey periods from NFHS-5 and SRS. Rank differences can be sensitive to sampling uncertainty.")


elif page=="Healthcare & districts":
    st.markdown('<div class="eyebrow">03 / Area indicators</div>',unsafe_allow_html=True)
    st.title("Healthcare & district insights")
    st.write("Two complementary views. The historical AHS scatter uses contemporaneous mortality and services; NFHS-5 shows newer service coverage only.")
    tab1,tab2=st.tabs(["AHS · same-period associations","NFHS-5 · 2019–21 services"])
    with tab1:
        section("2010–12 matched AHS panel","Healthcare vs historical infant mortality",
                "37 district averages per round · ecological correlation, not causal effect.")
        s1,s2=st.columns(2)
        with s1:w=st.selectbox("Matched survey round",["2010-11","2011-12"],index=1,key="healthwave")
        with s2:label=st.selectbox("Healthcare indicator",list(AHS_VARIABLES),key="healthfeat")
        feature=AHS_VARIABLES[label]
        scat,rho,pval,fdr=ecology(D,w,feature)
        c1,c2,c3=st.columns(3)
        with c1:box_metric("Spearman ρ",f"{rho:+.3f}","District-level rank correlation")
        with c2:box_metric("Districts","37","Same-period matched observations",BLUE)
        with c3:box_metric("BH adjusted p",f"{fdr:.3f}" if fdr is not None else "n/a",
                           "Only where included in 7-indicator testing family",ORANGE)
        fig=px.scatter(scat,x=feature,y="infant_imr",hover_name="District",
                       color_discrete_sequence=[MINT],
                       labels={feature:label+" (%)","infant_imr":"Infant deaths per 1,000"})
        fig.update_traces(marker=dict(size=13,line=dict(color="#071421",width=1.3),opacity=.8))
        chart_style(fig,460)
        st.plotly_chart(fig,width="stretch",config={"displaylogo":False})
        if fdr is None:
            st.caption("The displayed p-value was not pre-adjusted for this indicator. Interpret as exploratory.")
        else:
            st.caption(f"Unadjusted p={pval:.4f}; BH-adjusted p={fdr:.4f} within the seven prespecified tests for this round.")
        st.info("An ecological association does not demonstrate that a service prevents infant death. Underlying survey sampling uncertainty is not incorporated in these plotted correlations.")
        with st.expander("View matched values"):
            st.dataframe(scat.sort_values("infant_imr",ascending=False),hide_index=True,width="stretch")
    with tab2:
        section("Public NFHS-5 district facts","Indicators across all 38 districts",
                "Published indicators, 2019–21; no district infant mortality values in this source.")
        indicators=[x for x in D["nfhs"].columns if x!="District"]
        a,b=st.columns([1.2,.8])
        with a:ind=st.selectbox("Published healthcare / socioeconomic indicator",indicators,
                                index=indicators.index("Four or more ANC visits"))
        with b:sort=st.selectbox("Display order",["Highest first","Lowest first"])
        df=nfhs_sorted(D,ind,ascending=sort=="Lowest first")
        cols=st.columns(3)
        with cols[0]:box_metric("District mean",f"{df[ind].mean():.1f}%","Equal-district, not state weighted")
        with cols[1]:box_metric("Lowest",f"{df[ind].min():.1f}%",str(df.loc[df[ind].idxmin(),"District"]),BLUE)
        with cols[2]:box_metric("Highest",f"{df[ind].max():.1f}%",str(df.loc[df[ind].idxmax(),"District"]),ORANGE)
        q=st.slider("Districts to display",8,38,20,key="nfhsdistricts")
        plot_bar(df.head(q),"District",ind,MINT if "Anaemia" not in ind else ORANGE,
                 height=max(400,q*28),xaxis_title="Published indicator (%)")
        st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
        section("District profile","Compare available indicators")
        districts=st.multiselect("Districts",sorted(D["nfhs"]["District"].unique()),
            default=["Patna","Kishanganj","Madhepura"],max_selections=6)
        selectedinds=st.multiselect("Compare indicators",indicators,
          default=["Four or more ANC visits","Institutional births","Improved sanitation"],
          max_selections=6)
        if districts and selectedinds:
            comp=D["nfhs"].set_index("District").loc[districts,selectedinds].reset_index()
            long=comp.melt(id_vars="District",var_name="Indicator",value_name="Percent")
            fig=px.bar(long,x="Indicator",y="Percent",color="District",barmode="group",
              color_discrete_sequence=[MINT,BLUE,ORANGE,"#c4a4ff","#83c8e3","#f0d487"])
            fig.update_xaxes(tickangle=-20)
            chart_style(fig,440,legend=True)
            st.plotly_chart(fig,width="stretch",config={"displaylogo":False})
            st.dataframe(comp,hide_index=True,width="stretch")
        st.download_button("Export NFHS-5 public district indicators (CSV)",
             D["nfhs"].to_csv(index=False).encode("utf-8-sig"),
             "nfhs5_bihar_district_indicators_selected.csv","text/csv")
        st.caption("District service figures may have different denominators and age groups. The equal-district mean is not the official state prevalence.")


elif page=="Literature library":
    st.markdown('<div class="eyebrow">04 / Evidence & provenance</div>',unsafe_allow_html=True)
    st.title("Research literature library")
    st.write("Five primary research articles verified against full-text JATS XML and indexed in the local evidence database.")
    a,b,c=st.columns(3)
    with a:box_metric("Core studies","05","DOI-verified full texts")
    with b:box_metric("Extracted claims","21","With article/section locators",BLUE)
    with c:box_metric("Export format","RIS","For Zotero reference manager",ORANGE)
    q=st.text_input("Search paper titles, methods, findings, or tags",
                    placeholder="Try: leakage, birth weight, survival ...")
    article=D["papers"].copy()
    if q.strip():
        s=q.casefold()
        cols=["title","data","study_design_and_denominators",
              "outcome","main_reported_results","limitations","zotero_tags"]
        blob=article[cols].fillna("").astype(str).agg(" ".join,axis=1).str.casefold()
        article=article.loc[blob.str.contains(s,regex=False)]
    if article.empty:
        st.warning("No matching article in the five-paper core set.")
    for ix,(_,p) in enumerate(article.iterrows(),1):
        st.markdown(
            f'<div class="lit-card"><div class="lit-number">PRIMARY EVIDENCE · {escaped(p["year"])}</div>'
            f'<div class="lit-heading">{escaped(p["title"])}</div>'
            f'<div class="lit-sub"><b>Dataset / design:</b> '
            f'{escaped(p["study_design_and_denominators"])}<br>'
            f'<b>Reported:</b> {escaped(p["main_reported_results"])}<br>'
            f'<b>Limitation:</b> {escaped(p["limitations"])}</div></div>',
            unsafe_allow_html=True
        )
        st.markdown(f"[Open primary full text](https://pmc.ncbi.nlm.nih.gov/articles/{escaped(p['pmcid'])}/) · "
                    f"[DOI](https://doi.org/{escaped(p['doi'])})")
    ris=ROOT/"results/literature_core5/five_core_papers_zotero.ris"
    if ris.exists():
        st.download_button("Export five references to Zotero (.RIS)",
               ris.read_bytes(),"bihar_mortality_core5.ris","application/x-research-info-systems")
    st.info("Paper metrics are the authors’ reported results, not independently reproduced patient-level experiments. This is a selected five-paper register, not an exhaustive systematic review.")


elif page=="Research pipeline":
    st.markdown('<div class="eyebrow">05 / Methods & reproducibility</div>',unsafe_allow_html=True)
    st.title("Research pipeline")
    st.write("Transparent readiness checks for the data and modelling components.")
    status=readiness()
    a,b,c=st.columns(3)
    with a:box_metric("Protocol integrity",
       "Verified" if status["protocol_lock_valid"] else "Check required",
       "SHA-256 locked cohort definition",MINT if status["protocol_lock_valid"] else ORANGE)
    with b:box_metric("Available ecological data","Ready",
                       "AHS 37 historic districts / NFHS-5 38 districts",BLUE)
    with c:box_metric("NFHS individual BR","Pending",
                       "Authorized child-level files not confirmed",ORANGE)
    section("Implementation status","What is actually available")
    checks=[
      ("Historical AHS mortality","Published data & exploratory statistics","Ready",True),
      ("NFHS-5 district health indicators","Published district percentages","Ready",True),
      ("Literature evidence register","5 DOI-verified articles, 21 claims","Ready",True),
      ("Frozen NFHS cohort definition",status["protocol_id"],"Verified" if status["protocol_lock_valid"] else "Needs audit",status["protocol_lock_valid"]),
      ("Authorized NFHS-5 Births Recode","IIPS approval required","Not yet confirmed",False),
      ("Individual infant survival model","Never claim trained results without authorized microdata","Not trained",False),
      ("Official DHS synthetic-cohort IMR","Requires separately validated survey estimator","Not implemented",False),
    ]
    for title,desc,state,valid in checks:
        st.markdown(f'<div class="lit-card" style="margin:7px 0;padding:15px 18px">'
          f'<span style="color:{"#68e6c5" if valid else "#ffc58e"};font-weight:700">'
          f'{"●" if valid else "○"} {escaped(state)}</span>'
          f'<div style="color:#f2faf9;font-size:14px;font-weight:700;margin-top:6px">{escaped(title)}</div>'
          f'<div class="lit-sub">{escaped(desc)}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    section("Study design","Three fundamentally different analyses")
    for count,title,body in [
        ("01","Historical ecological study",
         "AHS 2010–13 district mortality; AHS 2010–12 matching healthcare measurements. Associations are not causal."),
        ("02","Published services exploration",
         "NFHS-5 2019–21 coverage and socioeconomic indicators for 38 districts; no individual death outcomes."),
        ("03","Future individual survival cohort",
         "Requires authorized NFHS-5 Births Recode, household/PSU isolation, censoring, calibration and survey-aware uncertainty."),
    ]:
        st.markdown(f'<div class="lit-card"><div class="lit-number">TRACK {count}</div>'
          f'<div class="lit-heading">{escaped(title)}</div>'
          f'<div class="lit-sub">{escaped(body)}</div></div>',unsafe_allow_html=True)
    with st.expander("See local launch and test commands"):
        st.code('cd D:\\InfantMortalityBihar\n'
                '.\\.venv\\Scripts\\python.exe -m pytest -q\n'
                '.\\.venv\\Scripts\\python.exe -m streamlit run bihar_research_dashboard.py',
                language="powershell")
    st.warning("For scientific and ethical reasons this app deliberately has no infant risk calculator or unvalidated healthcare recommendations.")


st.markdown(
    '<div class="smallfooter">BIHAR MORTALITY ATLAS · RESEARCH PREVIEW · '
    'Public data with documented source caveats · Not medical advice, clinical screening, '
    'or an official Bihar government dashboard.</div>',unsafe_allow_html=True
)
