## Why

The WalkabilityPrediction project has a working data pipeline skeleton but is incomplete: the EPA data download is broken, there is no feature engineering, no ML model, and no portfolio-ready output. Completing it produces a deployable, recruiter-facing data science project that demonstrates the full ML lifecycle — data acquisition, feature engineering, modeling, explainability, and AI-augmented analysis.

## What Changes

- Migrate from Jupyter notebook (`Walkability_Modeling.ipynb`) to a Marimo app (`main.py`) that runs as both an interactive notebook and a standalone script/web app
- Fix broken EPA National Walkability Index download (ZIP nested folder issue)
- Add feature engineering: ~10 OSM network metrics per Census block group (centrality, density, circuity, bearing entropy)
- Add XGBoost regression model predicting `NatWalkInd` from network features
- Add SHAP explainability plots
- Add Folium interactive choropleth map (predicted vs. actual walkability)
- Add Gemini AI chat with baked-in model context (SHAP summary, top/bottom neighborhoods)
- Move hardcoded Gemini API key from `chat.py` to `.env`
- Write README

## Capabilities

### New Capabilities

- `data-acquisition`: Download and cache OSM walk network, Census block groups, and EPA Walkability Index data for Central Austin
- `feature-engineering`: Compute OSM network metrics per block group (intersection density, street density, avg edge length, connectivity, circuity, bearing entropy, betweenness/closeness centrality)
- `walkability-model`: XGBoost regression model trained on network features to predict EPA National Walkability Index scores
- `explainability`: SHAP-based feature importance plots and per-neighborhood explanations
- `interactive-map`: Folium choropleth map visualizing predicted vs. actual walkability by block group
- `ai-chat`: Gemini-powered conversational interface with model results baked into context

### Modified Capabilities

*(none — this is a greenfield completion)*

## Impact

- `projects/WalkabilityPrediction/main.py` — rewritten as Marimo app (replaces placeholder)
- `projects/WalkabilityPrediction/chat.py` — API key moved to `.env`
- `projects/WalkabilityPrediction/.env` — new file (gitignored)
- `projects/WalkabilityPrediction/pyproject.toml` — add `marimo`, `python-dotenv` dependencies
- `Walkability_Modeling.ipynb` — retired (superseded by `main.py`)
