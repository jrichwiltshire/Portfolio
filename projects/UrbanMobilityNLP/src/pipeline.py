"""
NLP pipeline for the Urban Mobility Discourse Analyzer.

Stages: preprocessing -> embeddings -> topic modeling -> sentiment -> city
NER

Usage:
  uv run python src/pipeline.py
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# ------------------------------------------------------
# Stage 1 - Load & preprocess
# ------------------------------------------------------

_ARTIFACTS_RE = re.compile(
    r"\[deleted\]|\[removed\]"           # removed content markers
    r"|\[([^\]]+)\]\([^\)]+\)"           # markdown links → keep link text                                                                   
    r"|r/\w+"                            # subreddit mentions          
    r"|u/\w+"                            # user mentions               
    r"|https?://\S+",                    # bare URLs                 
    re.IGNORECASE,  
)

def preprocess(text: str) -> str:
    text = _ARTIFACTS_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text

def load_raw() -> pd.DataFrame:
    frames = [pd.read_parquet(p) for p in RAW_DIR.glob("*.parquet")]
    if not frames:
        raise FileNotFoundError("No raw Parquet files found. Run collect.py first.")
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset="post_id")
    df["clean_text"] = df["combined_text"].map(preprocess)
    df = df[df["clean_text"].str.len() >= 30].reset_index(drop=True)
    return df

# ------------------------------------------------------
# Stage 2 - Sentence embeddings
# ------------------------------------------------------
def compute_embeddings(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformers

    model = SentenceTransformers("all-MiniLM-L6-v2")
    embeddings = model.encode(
        texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True
    )
    return embeddings

# ------------------------------------------------------
# Stage 3 - Topic modeling (BERTopic)
# ------------------------------------------------------

def fit_topics(
    texts: list[str], embeddings: np.ndarray
) -> tuple:
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    umap_model = UMAP(
        n_neighbors=15, n_components=5, min_dist=0.0,
        metric="cosine", random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=30, metric="euclidean",
        cluster_selection_method="eom", prediction_data=True,
    )
    vectorizer = CountVectorizer(
        stop_words="english", min_df=3, ngram_range=(1, 2)
    )
    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        nr_topics="auto",
        calculate_probabilities=False,
        verbose=True,
    )
    topics, _ = topic_model.fit_transform(texts, embeddings)
    return topic_model, topics

def build_topic_info(topic_model) -> pd.DataFrame:
    rows = []
    for topic_id, words in topic_model.get_topics().items():
        top_words = [w for w, _ in words[:3]]
        label = "_".join([w for w, _ in words[:3]])
        count = len(topic_model.get_representative_docs(topic_id))
        rows.append({
            "topic_id": topic_id,
            "topic_label": label,
            "count": count,
            "top_words": json.dumps(top_words),
        })
    return pd.DataFrame(rows).sort_values("topic_id").reset_index(drop=True)

def compute_umap_2d(embeddings: np.ndarray) -> np.ndarray:
    from umap import UMAP

    reducer = UMAP(n_components=2, metric="cosine", random_state=42)
    return reducer.fit_transform(embeddings)

# ------------------------------------------------------
# Stage 4 - Sentiment analysis
# ------------------------------------------------------

def compute_sentiment(texts: list[str]) -> list[dict]:
    from transformers import pipeline as hf_pipeline

    print("Loading sentiment model (downloads ~480 MB on first run)...")
    sentiment_pipe = hf_pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-robert-base-sentiment-latest",
        tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
        top_k=None,
        truncation=True,
        max_length=512,
        device=-1, # CPU
    )

# ------------------------------------------------------
# Stage 5 - City NER
# ------------------------------------------------------

def extract_cities(texts: list[str]) -> list[str]:
    from cities import extract_city_mentions

    return [
        json.dumps(extract_city_mentions(t))
        for t in tqdm(texts, desc="City extraction")
    ]

# ------------------------------------------------------
# Main
# ------------------------------------------------------

def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Stage 1: Load & preprocess ===")
    df = load_raw()
    print(f"  {len(df)} posts loaded")
    texts = df["clean_text"].tolist()

    print("\n=== Stage 2: Embeddings ===")
    embeddings = compute_embeddings(texts)
    np.save(PROCESSED_DIR / "embeddings.npy", embeddings)
    print(f"  Saved embeddings {embeddings.shape}")

    print("\n=== Stage 3: Topic modeling ===")
    topic_model, topics = fit_topics(texts, embeddings)
    topic_info = build_topic_info(topic_model)
    topic_info.to_parquet(PROCESSED_DIR / "topic_info.parquet", index=False)

    # Map topic_id -> label
    id_to_label = dict(zip(topic_info["topic_id"], topic_info["topic_label"]))
    df["topic_id"] = topics
    df["topic_label"] = df["topic_id"].map(id_to_label).fillna("outlier")

    outlier_pct = (df["topic_id"] == -1).mean()
    print(f"  {len(topic_info)} topics | outlier rate: {outlier_pct:.1%}")

    print("\n Computing 2D UMAP for visualization...")
    coords_2d = compute_umap_2d(embeddings)
    umap_df = pd.DataFrame({"post_id": df["post_id"], "x": coords_2d[:, 0], "y": coords_2d[:, 1]})
    umap_df.to_parquet(PROCESSED_DIR / "umap_coords.parquet", index=False)

    print("\n===Stage 4: Sentiment ===")
    sentiment = compute_sentiment(texts)
    sent_df = pd.DataFrame(sentiment)
    for col in sent_df.columns:
        df[col] = sent_df[col].values

    print("\n=== Stage 5: City extraction ===")
    df["cities_mentioned"] = extract_cities(df["combined_text"].tolist())

    print("\n=== Saving posts_processed.parquet ===")
    keep_cols = [
        "post_id", "subreddit", "title", "combined_text",
        "score", "upvote_ratio", "num_comments", "created_utc",
        "author", "flair", "topic_id", "topic_label",
        "sentiment_label", "sentiment_positive", "sentiment_negative",
        "sentiment_compound", "cities_mentioned"
    ]
    df[keep_cols].to_parquet(PROCESSED_DIR / "posts_processed.parquet", index=False)
    print(f"  Saved {len(df)} posts -> data/processed/posts_processed.parquet")
    print("\nPipeline complete.")