import marimo as mo
import json
import pandas as pd
import plotly.express as px
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

@mo.cache
def load_data():
    posts = pd.read_parquet(DATA_DIR / "posts_procssed.parquet")
    posts["created_utc"] = pd.to_datetime(posts["created_utc"], utc=True)
    posts["cities_mentioned"] = posts["cities_mentioned"].apply(json.loads)
    posts["month"] = posts["created_utc"].dt.to_period("M").dt.to_timestamp()
    topic_info = pd.read_parquet(DATA_DIR / "topic_info.parquet")
    umap_coords = pd.read_parquet(DATA_DIR / "umap_coords.parquet")
    return posts, topic_info, umap_coords

posts, topic_info, umap_coords = load_data()