import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium", title="Austin Walkability Prediction")


@app.cell
def _():
    import io
    import os
    import warnings
    import zipfile
    from pathlib import Path

    import folium
    import geopandas as gpd
    import marimo as mo
    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    import osmnx as ox
    import pandas as pd
    import pygris
    import requests
    import shap
    import xgboost as xgb
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types
    from scipy.stats import entropy as scipy_entropy
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold, cross_val_predict

    warnings.filterwarnings("ignore")
    return (
        KFold,
        Path,
        cross_val_predict,
        folium,
        genai,
        gpd,
        io,
        load_dotenv,
        mean_squared_error,
        mo,
        np,
        nx,
        os,
        ox,
        pd,
        plt,
        pygris,
        r2_score,
        requests,
        scipy_entropy,
        shap,
        types,
        warnings,
        xgb,
        zipfile,
    )


@app.cell
def _(load_dotenv, os):
    load_dotenv()
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY not found - add it to .env")
    return (GEMINI_API_KEY,)


@app.cell
def _(Path):
    CENTER = (30.2672, -97.7431)  # Central Austin
    DIST_M = 3000  # 3 km radius
    CACHE_DIR = Path("cache")
    CACHE_DIR.mkdir(exist_ok=True)
    return (CACHE_DIR, CENTER, DIST_M)


@app.cell
def _(CACHE_DIR, CENTER, DIST_M, ox):
    _graph_path = CACHE_DIR / "osm_graph.graphml"
    if _graph_path.exists():
        G = ox.load_graphml(_graph_path)
        print("OSM graph loaded from cache.")
    else:
        G = ox.graph_from_point(CENTER, dist=DIST_M, network_type="walk", simplify=True)
        ox.save_graphml(G, _graph_path)
        print(f"OSM graph downloaded: {len(G.nodes):,} nodes, {len(G.edges):,} edges")
    G_proj = ox.project_graph(G)
    return (G, G_proj)


@app.cell
def _(CENTER, DIST_M, gpd, pygris):
    import shapely.geometry

    bg_travis = pygris.block_groups(state="TX", county="Travis", year=2020, cache=True)
    _study_circle = (
        gpd.GeoDataFrame(
            geometry=[shapely.geometry.Point(CENTER[1], CENTER[0])],
            crs="EPSG:4326",
        )
        .to_crs(bg_travis.crs)
        .buffer(DIST_M)
        .iloc[0]
    )
    bg_study = bg_travis[bg_travis.intersects(_study_circle)].copy()
    print(f"Block groups in study area: {len(bg_study)}")
    return (bg_study,)


@app.cell
def _(CACHE_DIR, gpd, io, pd, requests, zipfile):
    _cache_path = CACHE_DIR / "epa_walkability.parquet"
    if _cache_path.exists():
        epa_data = pd.read_parquet(_cache_path)
        print("EPA data loaded from cache.")
    else:
        _gdb_path = CACHE_DIR / "Natl_WI.gdb"
        if not _gdb_path.exists():
            print("Downloading EPA Walkability ZIP (405 MB, one-time)...")
            _url = "https://edg.epa.gov/EPADataCommons/public/OA/WalkabilityIndex.zip"
            _r = requests.get(_url, timeout=300)
            _z = zipfile.ZipFile(io.BytesIO(_r.content))
            _gdb_members = [f for f in _z.namelist() if f.startswith("Natl_WI.gdb")]
            _z.extractall(CACHE_DIR, members=_gdb_members)
            print("Extracted GDB.")
        print("Reading geodatabase...")
        _gdf = gpd.read_file(_gdb_path)
        _keep = [c for c in ["GEOID10", "GEOID20", "NatWalkInd"] if c in _gdf.columns]
        epa_data = pd.DataFrame(_gdf[_keep])
        for _col in ["GEOID10", "GEOID20"]:
            if _col in epa_data.columns:
                epa_data[_col] = epa_data[_col].astype(str)
        epa_data.to_parquet(_cache_path)
        print(f"EPA data saved: {len(epa_data):,} rows")
    return (epa_data,)


@app.cell
def _(bg_study, epa_data):
    _join_col = "GEOID20" if "GEOID20" in epa_data.columns else "GEOID10"
    bg_merged = bg_study.copy()
    bg_merged["GEOID"] = bg_merged["GEOID"].astype(str)
    bg_merged = bg_merged.merge(
        epa_data.rename(columns={_join_col: "GEOID"}),
        on="GEOID",
        how="left",
    ).dropna(subset=["NatWalkInd"])
    print(f"Block groups with walkability scores: {len(bg_merged)}")
    return (bg_merged,)


@app.cell
def _(CACHE_DIR, G_proj, np, nx, pd):
    _cache_path = CACHE_DIR / "centrality.parquet"
    if _cache_path.exists():
        centrality_df = pd.read_parquet(_cache_path)
        print("Centrality loaded from cache.")
    else:
        print("Computing centrality (approx betweenness k=500, ~60s)...")
        _betweenness = nx.betweenness_centrality(
            G_proj, k=500, normalized=True, weight="length"
        )
        _closeness = nx.closeness_centrality(G_proj, distance="length")
        centrality_df = pd.DataFrame(
            {"betweenness": _betweenness, "closeness": _closeness}
        )
        centrality_df.to_parquet(_cache_path)
        print("Centrality computed and cached.")
    return (centrality_df,)


@app.cell
def _(G, G_proj, bg_merged, centrality_df, gpd, np, ox, scipy_entropy):
    nodes, edges = ox.graph_to_gdfs(G_proj)

    # Degree and centrality on nodes
    nodes = nodes.copy()
    nodes["degree"] = nodes.index.map(dict(G_proj.degree()))
    nodes["betweenness"] = nodes.index.map(centrality_df["betweenness"])
    nodes["closeness"] = nodes.index.map(centrality_df["closeness"])

    # Bearings (must use unprojected graph for accurate angles)
    G_bearing = ox.bearing.add_edge_bearings(G)
    _, edges_b = ox.graph_to_gdfs(G_bearing)
    edges = edges.copy()
    edges["bearing"] = edges_b["bearing"].reindex(edges.index).values

    # Straight-line distance per edge -> circuity
    node_xy = nodes[["x", "y"]]
    edges_r = edges.reset_index()
    edges_r = edges_r.merge(
        node_xy.rename(columns={"x": "x_u", "y": "y_u"}),
        left_on="u",
        right_index=True,
        how="left",
    )
    edges_r = edges_r.merge(
        node_xy.rename(columns={"x": "x_v", "y": "y_v"}),
        left_on="v",
        right_index=True,
        how="left",
    )
    edges_r["sl_dist"] = np.sqrt(
        (edges_r["x_u"] - edges_r["x_v"]) ** 2 + (edges_r["y_u"] - edges_r["y_v"]) ** 2
    ).clip(lower=1)
    edges_r["circuity"] = edges_r["length"] / edges_r["sl_dist"]

    # Project block groups; compute area
    bg_proj = bg_merged.to_crs(nodes.crs)
    bg_proj = bg_proj.copy()
    bg_proj["area_km2"] = bg_proj.geometry.area / 1e6

    # Spatial join: nodes -> block groups
    nodes_j = gpd.sjoin(
        nodes.reset_index(),
        bg_proj[["GEOID", "geometry"]],
        how="left",
        predicate="within",
    )
    bg_node = (
        nodes_j.groupby("GEOID")
        .agg(
            intersection_count=("degree", lambda x: (x >= 3).sum()),
            streets_per_node_avg=("degree", "mean"),
            mean_betweenness=("betweenness", "mean"),
            max_betweenness=("betweenness", "max"),
            mean_closeness=("closeness", "mean"),
        )
        .reset_index()
    )

    # Spatial join: edges -> block groups
    edges_gdf = gpd.GeoDataFrame(edges_r, geometry="geometry", crs=nodes.crs)
    edges_j = gpd.sjoin(
        edges_gdf, bg_proj[["GEOID", "geometry"]], how="left", predicate="intersects"
    )
    bg_edge = (
        edges_j.groupby("GEOID")
        .agg(
            avg_edge_length=("length", "mean"),
            street_length_total=("length", "sum"),
            circuity_avg=("circuity", "mean"),
            bearing_entropy=(
                "bearing",
                lambda x: (
                    scipy_entropy(np.histogram(x.dropna() % 180, bins=36)[0] + 1)
                    if x.notna().any()
                    else 0.0
                ),
            ),
        )
        .reset_index()
    )

    # Assemble
    features = (
        bg_proj[["GEOID", "area_km2", "NatWalkInd", "geometry"]]
        .merge(bg_node, on="GEOID", how="left")
        .merge(bg_edge, on="GEOID", how="left")
    )
    features["intersection_density_km"] = (
        features["intersection_count"] / features["area_km2"]
    )
    features["street_density_km"] = (
        features["street_length_total"] / features["area_km2"]
    )
    FEATURE_COLS = [
        "intersection_density_km",
        "street_density_km",
        "avg_edge_length",
        "streets_per_node_avg",
        "circuity_avg",
        "bearing_entropy",
        "mean_betweenness",
        "max_betweenness",
        "mean_closeness",
    ]
    features[FEATURE_COLS] = features[FEATURE_COLS].fillna(0)
    features = features.dropna(subset=["NatWalkInd"])

    print(f"Feature matrix: {len(features)} rows * {len(FEATURE_COLS)} features")
    print(f"Null check: {features[FEATURE_COLS].isnull().sum().sum()} nulls")
    return (FEATURE_COLS, features)


@app.cell
def _(
    FEATURE_COLS,
    KFold,
    cross_val_predict,
    features,
    mean_squared_error,
    mo,
    np,
    r2_score,
    xgb,
):
    X = features[FEATURE_COLS].values
    y = features["NatWalkInd"].values

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        base_score=float(y.mean()),
        random_state=42,
    )

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = cross_val_predict(model, X, y, cv=cv)
    rmse = np.sqrt(mean_squared_error(y, oof_preds))
    r2 = r2_score(y, oof_preds)

    model.fit(X, y)
    features_out = features.copy()
    features_out["predicted_walkability"] = model.predict(X)

    print(f"CV RMSE: {rmse:.3f} | CV R^2: {r2:.3f}")
    return (X, features_out, model, oof_preds, r2, rmse, y)


@app.cell
def _(mo, np, oof_preds, plt, y):
    fig_resid, ax_resid = plt.subplots(figsize=(6, 6))
    ax_resid.scatter(y, oof_preds, alpha=0.4, edgecolors="none")
    _lim = [y.min(), y.max()]
    ax_resid.plot(_lim, _lim, "r--", lw=1)
    ax_resid.set_xlabel("Actual NatWalkInd")
    ax_resid.set_ylabel("Predicted NatWalkInd")
    ax_resid.set_title("Actual vs. Predicted Walkability (5-fold CV)")
    plt.tight_layout()
    return mo.as_html(fig_resid)


@app.cell
def _(FEATURE_COLS, X, features_out, mo, model, np, plt, shap):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    shap.summary_plot(shap_values, X, feature_names=FEATURE_COLS, show=False)
    fig_shap = plt.gcf()
    plt.tight_layout()

    # Build context string for Gemini
    _mean_abs = np.abs(shap_values).mean(axis=0)
    _ranked = sorted(zip(FEATURE_COLS, _mean_abs), key=lambda t: -t[1])
    _top5 = features_out.nlargest(5, "predicted_walkability")[
        ["GEOID", "predicted_walkability"]
    ].to_string(index=False)
    _bot5 = features_out.nsmallest(5, "predicted_walkability")[
        ["GEOID", "predicted_walkability"]
    ].to_string(index=False)

    shap_context = (
        "Global feature importances (ranked by mean |SHAP|):\n"
        + "\n".join(
            f" {i + 1}. {name}: {val:.4f}" for i, (name, val) in enumerate(_ranked)
        )
        + f"\n\nTop 5 most walkable block groups:\n{_top5}"
        + f"\n\nBottom 5 least walkable block groups:\n{_bot5}"
    )

    mo.output.append(mo.as_html(fig_shap))
    plt.close(fig_shap)
    return shap_context, shap_values


@app.cell
def _(CENTER, features_out, folium, mo):
    _m = folium.Map(location=CENTER, zoom_start=13, tiles="CartoDB positron")
    _gdf_wgs = features_out.to_crs("EPSG:4326")

    for _layer_name, _col in [
        ("Predicted Walkability", "predicted_walkability"),
        ("Actual Walkability", "NatWalkInd"),
    ]:
        folium.Choropleth(
            geo_data=_gdf_wgs.__geo_interface__,
            data=features_out,
            columns=["GEOID", _col],
            key_on="feature.properties.GEOID",
            fill_color="RdYlGn",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=_layer_name,
            name=_layer_name,
            show=(_layer_name == "Predicted Walkability"),
        ).add_to(_m)

    _tooltip_gdf = _gdf_wgs[
        ["GEOID", "predicted_walkability", "NatWalkInd", "geometry"]
    ].copy()
    _tooltip_gdf["predicted_walkability"] = _tooltip_gdf["predicted_walkability"].round(
        2
    )
    _tooltip_gdf["NatWalkInd"] = _tooltip_gdf["NatWalkInd"].round(2)

    folium.GeoJson(
        _tooltip_gdf,
        style_function=lambda f: {"fillOpacity": 0, "weight": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=["GEOID", "predicted_walkability", "NatWalkInd"],
            aliases=["Block Group:", "Predicted:", "Actual:"],
        ),
    ).add_to(_m)

    folium.LayerControl().add_to(_m)
    return mo.Html(_m._repr_html_())


@app.cell
def _(GEMINI_API_KEY, genai, mo, shap_context, types):
    _client = genai.Client(api_key=GEMINI_API_KEY)
    _system_prompt = (
        "You are an expert in urban walkability and data science. "
        "You have access to results from an XGBoost model predicted EPA National Walkability Index scores "
        "for Census block groups in Central Austin, TX (3km radius), using OpenStreetMap street network features.\n\n"
        + shap_context
    )

    def _call_gemini(messages, config):
        _contents = [
            types.Content(
                role="user" if msg.role == "user" else "model",
                parts=[types.Part(text=msg.content)],
            )
            for msg in messages
        ]
        return _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=_contents,
            config=types.GenerateContentConfig(system_instruction=_system_prompt),
        ).text

    chat = mo.ui.chat(
        _call_gemini,
        prompts=[
            "What is the most important factor driving walkability in Austin?",
            "Which neighborhoods are most walkable and why?",
            "What could make the least walkable areas better?",
        ],
    )
    return chat


if __name__ == "__main__":
    app.run()
