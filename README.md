# EconViz Lab

An interactive explorer for cross-country macroeconomic indicators. It retrieves annual data from the World Bank's World Development Indicators API, preserves missing observations, and displays indicators in separate small multiples so different units are never silently mixed on one axis.

## Features

- Official WDI API data; no API key required.
- Real GDP growth, CPI inflation, and unemployment (ILO modelled estimate).
- Country and year-range filters, source-linked export, and retrieval timestamp.
- No interpolation or causal claims. Missing data remain missing.
- User-defined percentage-point shocks allow a transparent one-year scenario view alongside history. These are assumptions supplied by the user, not model forecasts.

The separate time-series panels follow the comparison layout of AnyPlot's [multi-line Plotly chart](https://anyplot.ai/line-multi/python/plotly), adapted here so GDP growth, inflation, and unemployment keep independent axes. Chart code is rebuilt for this app; the data and analytical choices are project-specific.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

World Bank API documentation: [Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation) and [basic call structure](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures). The World Bank notes that WDI indicators compile data from officially recognized sources; indicator definitions and source notes remain authoritative for interpretation.

Attribution: World Bank, World Development Indicators, retrieved via the World Bank Indicators API. WDI is generally available under [CC BY 4.0](https://datacatalog.worldbank.org/public-licenses), but some indicator inputs may be subject to third-party terms. Check the relevant indicator metadata before redistributing exported data. This project is not affiliated with or endorsed by the World Bank.

## Data quality and interpretation

The app stores the country code, indicator code, observation year, value, source URL, and retrieval timestamp with exports. API data can be revised between runs, so an export is a point-in-time snapshot. The unemployment series is modelled and should not be treated as a direct count. Cross-country comparisons can be affected by definitions, coverage, revisions, and missingness. GDP growth and inflation are shown as reported annual percent changes; do not infer causality from co-movement.

## Checks

```bash
python -m pytest
```

## License

MIT. See `LICENSE`.
