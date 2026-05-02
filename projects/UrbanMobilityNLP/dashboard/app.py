from openpyxl.chart import legend
import marimo as mo
import json
import pandas as pd
import plotly.express as px
from pathlib import Path

# __file__ is dashboard/app.py so .parent.parent goes up to the project
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

# @mo.cache memoizes this function for the lifetime of the session
# Without it, Mariom would re-read all three Parquet files every time
# any widget changes - which would make the app feel really slow.
@mo.cache
def load_data():
    posts = pd.read_parquet(DATA_DIR / "posts_procssed.parquet")

    # Parquet stores timestamps as UTC but pandas doesn't always infer that
    # utc=True ensures timezone-aware datetimes throughout.
    posts["created_utc"] = pd.to_datetime(posts["created_utc"], utc=True)

    # cities_mentioned was saved as a JSON string (e.g. '["Amsterdam", "Austin"]')
    # because Parquet doesn't natively store Python lists. json.loads converts
    # each string back into an actual list so we can call .explode() later.
    posts["cities_mentioned"] = posts["cities_mentioned"].apply(json.loads)

    # to_period("M") snaps each timestamp to its month (e.g. 2024-03),
    # then to_timestamp() converts it back to a datetime so Plotly can plot it
    # on a time axis. Used in sentiment timeline
    posts["month"] = posts["created_utc"].dt.to_period("M").dt.to_timestamp()
    topic_info = pd.read_parquet(DATA_DIR / "topic_info.parquet")
    umap_coords = pd.read_parquet(DATA_DIR / "umap_coords.parquet")
    return posts, topic_info, umap_coords

posts, topic_info, umap_coords = load_data()

# mo.ui widgets are Marimo's reactive controls. When a widget's value changes,
# every cell that references .value on that widget automatically re-executes.                           
# This is the core of Marimo's reactivity — no callbacks needed. 

subreddit_filter = mo.ui.multiselect(
    options=sorted(posts["subreddit"].unique().tolist()),
    value=sorted(posts["subreddit"].unique().tolist()),
    label="Subreddits",
)
date_range = mo.ui.date_range(
    start=posts["created_utc"].min().date(),
    stop=posts["created_utc"].max().date(),
    label="Date Range",
)

# "All" is a sentinel value - when it's selected we skip the topic filter entirely
topic_options = ["All"] + sorted(
    topic_info[topic_info["topic_id"] != -1]["topic_label"].tolist()
)
topic_filter = mo.ui.multiselect(
    options=topic_options,
    value="All",
    label="Topics",
)

# mo.hstack lays elements out horizontally; justify="start" left-aligns them.
# mo.vstack is the vertical equivalent - used heavily inside each panel function.
mo.hstack([subreddit_filter, date_range, topic_filter], justify="start")

def apply_filters(df):
    # Build a boolean mask by combining each active filter with &=
    mask = df["subreddit"].isin(subreddit_filter.value)
    mask &= df["created_utc"].dt.date >= date_range.value[0]
    mask &= df["created_utc"].dt.date <= date_range.value[1]

    # Only apply the topic filter if the user has deselected "All"
    if "All" not in topic_filter.value and topic_filter.value:
        mask &= df["topic_label"].isin(topic_filter.value)

    # .copy() is important in Marimo: mutating a DataFrame in-place doesn't
    # trigger reactivity. Always return a new object so downstream cells
    # see the change and re-execute.
    return df[mask].copy()

# This cell reads all three widget values, so Marimo re-runs it - and
# everything that depends on `filtered` - whenever any widget changes.
filtered = apply_filters(posts)

def overview_panel(df):
    avg_sent = df["sentiment_compound"].mean()
    # Visual cue: green if net positive, red if net negative, yellow if neutral.
    # The 0.05 threshold avoids flipping colour on near-zero scores.
    sent_emoji = "🟢" if avg_sent > 0.05 else "🔴" if avg_sent < -0.05 else "🟡"
    
    # mo.stat renders a labelled metric card - good for at-a-glance KPIs.
    stats = mo.hstack([
        mo.stat(value=f"{len(df):,}", label="Posts"),
        mo.stat(value=str(df["subreddit"].nunique()), label="Subreddits"),
        mo.stat(
            value=f"{df['created_utc'].min().strftime('%b %Y')} - {df['created_utc'].max().strftime('%b %Y')}",
            label="Date Range",
        ),
        mo.stat(
            value=f"{sent_emoji} {avg_sent:+.2f}",
            label="Avg Sentiment",
        ),
    ])
    counts = df.groupby("subreddit").size().reset_index(name="posts")

    # px (Plotly Express) is a high-level Plotly API - one line per chart type.
    # Pass the figure to mo.as_html() to render it inside Marimo.
    fig = px.bar(
        counts, x="subreddit", y="posts", color="subreddit",
        title="Posts by Subreddit", labels={"subreddit": "", "posts": "Post Count"},
    )
    fig.update_layout(showlegend=False)
    return mo.vstack([stats, mo.as_html(fig)])

def topic_panel(df, coords, tinfo):
    # Join the UMAP 2D coordinates onto the filtered posts so we only plot
    # the posts that survive the current filter selection.
    plot_df = df.merge(coords, on="post_id", how="inner")

    # Each dot is a Reddit post. Color = BERTopic cluster.
    # hover_data controls what appears in the tooltip; setting x/y to False
    # hides the raw coordinate values from the tooltip.
    fig = px.scatter(
        plot_df, x="x", y="y", color="topic_label",
        hover_data={"title": True, "subreddit": True, "sentiment_label": True, "x": False, "y": False},
        title="Topic Clusters (UMAP)",
        labels={"topic_label": "Topic"},
        opacity=0.6,
    )
    fig.update_traces(marker_size=4)
    fig.update_layout(legend=dict(itemsizing="constant"))

    # Only show topic rows that are visible in the current filtered scatter
    visible_topics = tinfo[tinfo["topic_label"].isin(plot_df["topic_label"].unique())]
    display_cols = ["topic_label", "count", "top_words"]

    # mo.ui.table renders an interactive sortable table with optional pagination.
    # pagination=True adds next/prev controls instead of dumping all rows at once.
    return mo.hstack([
        mo.vstack([
            mo.md("### Topics in view"),
            mo.ui.table(visible_topics[display_cols].rename(columns={
                "topic_label": "Topic", "count": "Posts", "top_words": "Top Words"
            }), pagination=True),
        ]),
        mo.as_html(fig),
    ])

def sentiment_panel(df):
    # Group by month x subreddit and take the mean sentiment score. 
    # This smooths out individual post noise and shows macro trends
    monthly = (
        df.groupby(["month", "subreddit"])["sentiment_compound"]
        .mean()
        .reset_index()
    )
    # Convert to string so Plotly treats it as a categorical axis,
    # which avoids gaps for months with no data.
    monthly["month"] = monthly["month"].astype(str)

    line_fig = px.line(
        monthly, x="month", y="sentiment_compound", color="subreddit",
        title="Mean Sentiment Over Time",
        labels={"sentiment_compound": "Sentiment (-1 to +1)", "month": ""},
    )
    # A dashed zero line makes it easy to see when a subreddit crosses
    # from net-negative to net-positive discourse (or vice-versa).
    line_fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    hist_fig = px.histogram(
        df, x="sentiment_compound", color="subreddit", barmode="overlay",
        opacity=0.6, title="Sentiment Distribution by Subreddit",
        labels={"sentiment_compound": "Sentiment (-1 to +1)"},
        nbins=40
    )

    # mo.callout renders a highlighted info/warning box - useful for
    # surfacing caveats that a portfolio viewer needs to interpret the data
    # correctly.
    fuckcars_note = mo.callout(
        mo.md(
            "**Note on r/fuckcars:** Negative sentiment here often reflets hostility "
            "*toward car culture*, not toward cycling or walkability."
        ),
        kind="warn",
    )
    return mo.vstack([fuckcars_note, mo.as_html(line_fig), mo.as_html(hist_fig)])

def city_panel(df):
    # .explode() turns each row with a list like ["Amsterdam", "Austin"] into
    # two separate rows - one per city. This lets us groupby city downstream.
    city_df = df.explode("cities_mentioned").dropna(subset=["cities_mentioned"])
    city_df = city_df.rename(columns={"cities_mentioned": "city"})
    city_df = city_df[city_df["city"].str.strip() != ""]

    top_cities = (
        city_df.groupby("city").size()
        .reset_index(name="mentions")
        .sort_values("mentions", ascending=False)
        .head(20)
    )
    bar_fig = px.bar(
        top_cities, x="city", y="mentions",
        title="Top 20 Most-Mentioned Cities",
        labels={"city": "", "mentions": "Mention Count"},
    )
    bar_fig.update_xaxes(tickangle=45)

    # Box plot shows the full sentiment distribution per city, not just the mean.
    # This reveals whether a city is consistently discussed positively,
    # negatively, or whether opinions are polarised (wide box).
    top15 = top_cities.head(15)["city"].tolist()
    box_df = city_df[city_df["city"].isin(top15)]
    box_fig = px.box(
        box_df, x="city", y="sentiment_compound", color="city",
        title="Sentiment Distribution - Top 15 Cities",
        labels={"city": "", "sentiment_compound": "Sentiment (-1 to +1)"},
    )
    box_fig.update_layout(showlegend=False)
    box_fig.update_xaxes(tickangle=45)
    box_fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    return mo.vstack([mo.as_html(bar_fig), mo.as_html(box_fig)])

def browser_panel(df):
    # A local widget defined inside a function - Marimo handles this correctly.
    # The widget and the table it filters are returns together in a vstack,
    # so they stay coupled visually and reactively.
    city_search = mo.ui.text(placeholder="Filter by city...", label="City search")

    display = df.copy()
    if city_search.value:
        term = city_search.value.strip().lower()
        # cities mentioned is a list per row, so we check if any city in the list
        # contains the search term (case-insensitive substring match).
        display = display[
            display["cities_mentioned"].apply(
                lambda cities: any(term in c.lower() for c in cities)
            )
        ]

    table_df = display[
        ["created_utc", "subreddit", "topic_label", "sentiment_label", "title"]
    ].copy()
    table_df["created_utc"] = table_df["created_utc"].dt.strftime("%Y-%m-%d")
    table_df = table_df.rename(columns={
        "created_utc": "Date", "subreddit": "Subreddit",
        "topic_label": "Topic", "sentiment_label": "Sentiment", "title": "Title",
    })
    return mo.vstack([city_search, mo.ui.table(table_df, pagination=True)])

# mo.ui.tabs takes a dict of {tab_name: content}.
# Each value is a Marimo element (mo.vstack, mo.hstack, mo.as_html, etc.).
# The panel functions are called here with `filtered`, so every tab
# reflects the same global filter state.
tabs = mo.ui.tabs({
    "Overview": overview_panel(filtered),
    "Topic Explorer": topic_panel(filtered, umap_coords, topic_info),
    "Sentiment Timeline": sentiment_panel(filtered),
    "City Comparison": city_panel(filtered),
    "Post Browser": browser_panel(filtered),
})
tabs