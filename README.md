# Bihar Mortality Atlas

Streamlit dashboard exploring historical Bihar infant mortality (AHS 2010–13),
district healthcare/socioeconomic published indicators (NFHS-5, 2019–21),
and peer-reviewed literature. **Not a clinical app or infant risk estimator.**

## Public deployment

1. Publish THIS deployment folder as a **new** GitHub repository.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Choose **Create app** and **Yup, I have an app**.
4. Select the newly created repository, branch `main`, entrypoint `bihar_research_dashboard.py`.
5. Choose Python 3.12 in the deployment UI if available, and deploy.

Cloud should install packages from `requirements.txt` automatically.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run bihar_research_dashboard.py
```

## Data provenance and limitations

- Only published/derived AHS and NFHS district aggregates are included.
- AHS mortality district data are **historical 2010–13** (37 historical districts).
- NFHS-5 indicator data are for **2019–21**, describing 38 districts.
- Historical AHS mortality and newer NFHS service coverage must **not** be merged as contemporaneous observations.
- NFHS district indicator averages shown are unweighted district means, NOT official Bihar state rates.
- AHS scatterplot correlations are exploratory ecological statistics, not causal effects.
- Literature is a five-paper selected reference register, not an exhaustive systematic review.
- No individual NFHS microdata, restricted child records, patient predictions, model weights or credentials are packaged.
- The protocol lock and referenced source files are public research code/documentation, not NFHS microdata.

## Deployment content

`bihar_research_dashboard.py` and `src/dashboard_data.py` load only published CSV
inputs under `data/public/official/derived`, `results/nfhs5_district`,
`results/ahs_historical_study`, and `results/literature_core5`.

## Source / data access

- Annual Health Survey: NHSRC https://qps.nhsrcindia.org/annual-health-survey
- Public NFHS-5 district indicators: https://github.com/pratapvardhan/NFHS-5
- Official NFHS reports: https://www.nfhsiips.in/
- Core paper DOI and original article source paths in `results/literature_core5/papers.csv`.

## Security

Never commit `/data/raw`, restricted NFHS BR files, tokens, cookies, or secrets.
Review public repo visibility and Streamlit privacy settings before sharing externally.
