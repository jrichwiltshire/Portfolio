## Context

The project has a partially-working Jupyter notebook targeting Central Austin (3km radius from city center). OSM network download and Census block group fetching work; EPA data download is broken. All necessary ML dependencies are already installed. The goal is a single `main.py` Marimo app that serves as both development notebook and deployable portfolio artifact.

## Goals / Non-Goals

**Goals:**
- One `main.py` that works as `python main.py`, `marimo edit main.py`, and `marimo run main.py`
- End-to-end pipeline: data → features → model → explainability → map → chat
- Disk-caching of slow operations (OSM download, centrality computation) so reruns are fast
- Gemini chat that knows the model results (not a generic chatbot)

**Non-Goals:**
- Generalization beyond Central Austin 3km study area
- Real-time data updates
- User authentication or multi-user state
- Predicting walkability for locations with no OSM data

## Decisions

### D1: Marimo over plain script
Marimo files are valid `.py` files that also run as reactive notebooks and web apps. This eliminates the notebook-to-script translation step and makes `marimo run main.py` a zero-effort portfolio demo URL.
*Alternatives considered*: Plain script (no interactive exploration), Jupyter (requires separate production file), Streamlit (heavier, separate file still needed).

### D2: Centrality computed on full graph, then spatially joined
Betweenness centrality is a global property — a node's importance depends on the entire network, not just its block group. Computing on full graph then joining preserves this. Approximate betweenness (`k=500`) keeps runtime under ~60 seconds for the 19k-node Austin graph.
*Alternatives considered*: Per-block-group subgraph centrality (loses cross-block-group paths, inaccurate).

### D3: `ox.stats.basic_stats()` as the primary feature source
OSMnx's built-in stats function computes intersection density, street density, circuity, edge length distribution, and connectivity in one call, correctly handling projections and area calculation. This avoids reimplementing well-tested spatial math.

### D4: Bearing entropy as a grid-regularity feature
Shannon entropy of street bearing distribution captures how grid-like a neighborhood is. Low entropy = regular grid (downtown) → tends to be more walkable. This is not captured by density metrics alone.

### D5: SHAP values serialized and passed to Gemini as context
After model training, SHAP global feature importances and the top 5 / bottom 5 neighborhoods by predicted score are serialized to a compact string and injected into the Gemini system prompt. This makes the chat genuinely model-aware without requiring Gemini to re-run any computation.

### D6: `.env` for secrets, `python-dotenv` for loading
Standard pattern. `.env` is gitignored. `chat.py` is absorbed into `main.py`; the standalone file is retired.

### D7: Disk cache with `joblib.Memory` or manual JSON/parquet
Slow steps (OSM graph download, centrality, EPA download) are cached to `cache/` using either `joblib.Memory` or manual serialization. Marimo's reactivity means re-running a cell only recomputes if inputs changed — caching makes the first run fast enough to not frustrate.

## Risks / Trade-offs

- **EPA ZIP structure** → The existing notebook fails because the CSV is nested in a subfolder. Mitigation: list all ZIP contents and find the CSV regardless of depth (`next(f for f in z.namelist() if f.endswith('.csv'))`).
- **Centrality runtime** → Full betweenness on 19k nodes with k=500 takes ~30-60s. Mitigation: cache result to `cache/centrality.parquet` and skip recomputation if file exists.
- **Block group count vs. model size** → 766 block groups is a small dataset for XGBoost. Mitigation: use `n_estimators=200`, `max_depth=4`, `learning_rate=0.05` with early stopping; validate with 5-fold CV rather than a train/test split to maximize data use.
- **Marimo reactivity and side effects** → Marimo's reactive execution model means cells with side effects (file writes, API calls) need care. Mitigation: wrap slow/side-effectful operations in `@app.cell` with explicit dependency args.

## Migration Plan

1. Add `marimo` and `python-dotenv` to `pyproject.toml`
2. Create `.env` with `GEMINI_API_KEY=...`; add `.env` to `.gitignore`
3. Rewrite `main.py` as Marimo app (sections map to proposal capabilities)
4. Verify `python main.py` runs clean
5. Verify `marimo run main.py` serves the web app
6. Archive `Walkability_Modeling.ipynb` and `chat.py` (or delete after user confirmation)

## Open Questions

- Should the Folium map be embedded in the Marimo app (as an `mo.Html` component) or saved to `output/map.html`? Embedding keeps everything in one place; saving allows standalone sharing.
- Should bearing entropy be computed per block group (from edges within polygon) or from the full graph? Per-block-group is more locally meaningful; full-graph is faster.
