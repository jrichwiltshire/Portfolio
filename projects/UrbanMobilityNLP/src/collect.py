"""
Reddit data collection for the Urban Mobility Discourse Analyzer.

Usage:
    uv run python src/collect.py                # full collection
    uv run python src/collect.py --limit 50    # quick test
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import praw
from dotenv import load_dotenv
import os

load_dotenv()

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
CACHE_FILE = ROOT / "data" / "cache" / "collection_state.json"

SUBREDDITS = [
    "urbanplanning",
    "bikecommuting",
    "fuckcars",
    "strongtowns",
    "transit"
]

def load_cache() -> dict[str, set[str]]:
    if CACHE_FILE.exists():
        raw = json.loads(CACHE_FILE.read_text())
        return {k: set(v) for k, v in raw.items()}
    return {}

def save_cache(cache: dict[str, set[str]]) -> None:
    CACHE_FILE.write_text(
        json.dumps({k: list(v) for k, v in cache.items()}, indent=2)
    )

def make_reddit() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )

def collect_subreddit(
    reddit: praw.Reddit,
    subreddit_name: str,
    limit: int,
    seen_ids: set[str],
) -> list[dict]:
    sub = reddit.subreddit(subreddit_name)
    posts: dict[str, dict] = {}

    def fetch(listing):
        for submission in listing:
            if submission.id in seen_ids or submission.id in posts:
                continue
            body = submission.selftext or ""
            if body in ("[deleted]", "[removed]"):
                body = ""
            combined = f"{submission.title} {body}".strip()
            if len(combined) < 30:
                continue
            posts[submission.id] = {
                "post_id": submission.id,
                "subreddit": subreddit_name,
                "title": submission.title,
                "body": body,
                "combined_text": combined,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "created_utc": datetime.fromtimestamp(
                    submission.created_utc, tz=timezone.utc
                ),
                "url": submission.url,
                "author": str(submission.author) if submission.author else "[deleted]",
                "flair": submission.link_flair_text,
            }

    fetch(sub.hot(limit=limit))
    fetch(sub.top(time_filter="year", limit=limit))
    fetch(sub.new(limit=limit))

    return list(posts.values())

def main(limit: int) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    reddit = make_reddit()
    cache = load_cache()
    date_tag = datetime.now().strftime("%Y%m%d")

    for subreddit_name in SUBREDDITS:
        print(f"\nCollecting r/{subreddit_name}...")
        seen_ids = cache.get(subreddit_name, set())
        posts = collect_subreddit(reddit, subreddit_name, limit, seen_ids)
        print(f"  {len(posts)} new posts")

        if posts:
            df = pd.DataFrame(posts)
            out_path = RAW_DIR / f"{subreddit_name}_{date_tag}.parquet"
            df.to_parquet(out_path, index=False)
            print(f"  Saved -> {out_path.name}")
            cache[subreddit_name] = seen_ids | {p["post_id"] for p in posts}
            save_cache(cache)

        time.sleep(1)

    print("\nDone. Cache updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    main(args.limit)