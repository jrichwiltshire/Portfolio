# Urban Mobility Discourse Analyzer

An NLP-powered interactive dashboard that mines Reddit discussions about walkable cities, cycling infrastructure, and urban transit — then surfaces trends, sentiment, and city-level insights through a reactive Marimo app.

## What It Does

1. **Collects** posts from five urban-planning/active-transportation subreddits via the Reddit API
2. **Embeds** each post using a sentence transformer model (`all-MiniLM-L6-v2`)
3. **Clusters** posts into coherent topics with BERTopic (UMAP + HDBSCAN)
4. **Scores** sentiment with a RoBERTa model trained on informal social text
5. **Extracts** city mentions via regex matching against a curated city list
6. **Visualizes** everything in a five-tab Marimo dashboard

## Subreddits Analyzed

| Subreddit | Focus |
|---|---|
| r/urbanplanning | City design, zoning, transit policy |
| r/bikecommuting | Cycling as everyday transportation |
| r/fuckcars | Car-free advocacy and infrastructure critique |
| r/notjustbikes | Evidence-based urbanism |
| r/transit | Public transportation systems |

## NLP Stack

| Component | Model / Library |
|---|---|
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Topic modeling | BERTopic (UMAP + HDBSCAN + CountVectorizer) |
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` |
| City extraction | Regex matching against curated city list |
| Dimensionality reduction | UMAP (5D for BERTopic, 2D for visualization) |

## Dashboard Panels

- **Overview** — corpus stats and post volume by subreddit
- **Topic Explorer** — interactive UMAP scatter colored by topic cluster
- **Sentiment Timeline** — sentiment trends over time per subreddit
- **City Comparison** — most-discussed cities and their sentiment profiles
- **Post Browser** — searchable, filterable table of raw posts

## Setup

### 1. Get Reddit API credentials

Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps), create a **script**-type app, and note your client ID and secret.

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Install dependencies

> Note: `torch` is ~2–3 GB and the sentiment model is ~480 MB. First run will download both automatically.

```bash
uv sync
```

### 4. Collect data

```bash
# Quick test (50 posts per subreddit)
uv run python src/collect.py --limit 50

# Full collection (~1000+ posts per subreddit)
uv run python src/collect.py
```

### 5. Run NLP pipeline

```bash
uv run python src/pipeline.py
```

### 6. Launch dashboard

```bash
uv run marimo run dashboard/app.py
```

For development (editable notebook view):

```bash
uv run marimo edit dashboard/app.py
```

## Known Limitations

- Reddit's API caps results at ~1,000 posts per listing endpoint per sort method. The collector fetches `hot`, `top`, and `new` separately to maximize yield, but historical coverage is not complete.
- r/fuckcars sentiment: negative scores in this subreddit often reflect negativity *toward car culture*, not toward urbanism. A contextual note is shown in the dashboard.
- The NLP pipeline runs on CPU by default and takes ~15–30 minutes for ~5,000 posts.

## Skills Demonstrated

- NLP pipeline design (embeddings, topic modeling, sentiment analysis, NER)
- BERTopic with custom UMAP/HDBSCAN configuration
- HuggingFace Transformers for inference
- Marimo reactive dashboard development
- Plotly interactive visualization
- Reddit API data collection with PRAW
- Parquet-based data storage
