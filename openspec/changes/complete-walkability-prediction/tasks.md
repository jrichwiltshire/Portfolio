## 1. Project Setup

- [x] 1.1 Add `marimo` and `python-dotenv` to `pyproject.toml` and run `uv sync`
- [ ] 1.2 Create `.env` file with `GEMINI_API_KEY=<your-key>` and add `.env` to `.gitignore`
- [ ] 1.3 Delete or archive `Walkability_Modeling.ipynb` and `chat.py`

## 2. Data Acquisition (main.py — Section 1)

- [x] 2.1 Scaffold `main.py` as a Marimo app (import `marimo as mo`, define `app = mo.App()`)
- [x] 2.2 Add OSM walk network cell: download with `ox.graph_from_point`, cache to `cache/osm_graph.graphml`, load from cache if file exists
- [x] 2.3 Add Census block groups cell: download with `pygris.block_groups`, filter to study area polygon, reproject consistently
- [x] 2.4 Fix EPA download cell: find CSV at any ZIP nesting depth using `next(f for f in z.namelist() if f.endswith('.csv'))`, extract `GEOID20`/`GEOID10` and `NatWalkInd`
- [x] 2.5 Add merge cell: join EPA scores onto block group GeoDataFrame by GEOID, drop rows with null `NatWalkInd`

## 3. Feature Engineering (main.py — Section 2)

- [x] 3.1 Add centrality cell: compute approximate betweenness (`k=500`) and closeness centrality on full projected graph; cache node-level results to `cache/centrality.parquet`
- [x] 3.2 Add spatial join cell: join node centrality values to block groups (mean and max per block group); fill missing values with 0
- [x] 3.3 Add basic stats cell: for each block group, compute `ox.stats.basic_stats()` on the edges intersecting that polygon (intersection density, street density, avg edge length, streets per node, circuity)
- [x] 3.4 Add bearing entropy cell: compute Shannon entropy of edge bearing distribution per block group
- [x] 3.5 Assemble final feature matrix: combine all features into a clean DataFrame with no NaN values; print shape and column list

## 4. ML Model (main.py — Section 3)

- [x] 4.1 Add model cell: define XGBoost regressor (`n_estimators=200`, `max_depth=4`, `learning_rate=0.05`); run 5-fold cross-validation; report mean/std RMSE and R²
- [x] 4.2 Generate out-of-fold predictions for all block groups; attach `predicted_walkability` column to the GeoDataFrame
- [x] 4.3 Add residual plot cell: matplotlib scatter of actual vs. predicted with identity line

## 5. Explainability (main.py — Section 4)

- [x] 5.1 Add SHAP cell: fit `shap.TreeExplainer` on full trained model; compute SHAP values for all samples
- [x] 5.2 Render SHAP beeswarm summary plot
- [x] 5.3 Build SHAP context string: rank features by mean |SHAP|; identify top 5 and bottom 5 block groups by predicted score with their dominant SHAP feature; serialize to plain-text string for Gemini prompt

## 6. Interactive Map (main.py — Section 5)

- [x] 6.1 Add Folium map cell: create choropleth of predicted walkability (RdYlGn color scale, centered on study area)
- [x] 6.2 Add second choropleth layer for actual `NatWalkInd` with Folium layer control toggle
- [x] 6.3 Add tooltips to each block group showing GEOID, predicted score, actual score, and top SHAP feature
- [x] 6.4 Embed Folium map in Marimo app using `mo.Html(map._repr_html_())`

## 7. AI Chat (main.py — Section 6)

- [x] 7.1 Add env loading cell: `load_dotenv()` at app start; raise clear error if `GEMINI_API_KEY` is missing
- [x] 7.2 Build Gemini system prompt: inject study area description + SHAP context string from step 5.3
- [x] 7.3 Implement chat cell using `mo.ui.chat` backed by Gemini API (`gemini-2.0-flash`); maintain conversation history across turns

## 8. Polish

- [ ] 8.1 Verify `python main.py` runs end-to-end without error
- [ ] 8.2 Verify `marimo run main.py` serves the app in browser
- [ ] 8.3 Write README: project description, setup instructions (`uv sync`, `.env`), run commands (`python main.py`, `marimo run main.py`)
