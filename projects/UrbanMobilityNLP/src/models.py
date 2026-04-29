from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class RawPost:
    post_id: str
    subreddit: str
    title: str
    body: str
    combined_text: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    url: str
    author: str
    flair: str | None

@dataclass
class ProcessedPost:
    post_id: str
    subreddit: str
    title: str
    combined_text: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    author: str
    flair: str | None
    topic_id: int = -1
    topic_label: str = "outlier"
    sentiment_label: str = ""
    sentiment_positive: float = 0.0
    sentiment_negative: float = 0.0
    sentiment_compound: float = 0.0
    cities_mentioned: list[str] = field(default_factory=list)

@dataclass
class TopicInfo:
    topic_id: int
    topic_label: str
    count: int
    top_words: list[str]