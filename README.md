# Jared R. Wiltshire — Data Science & Analytics Portfolio

## About

Data Scientist with 10+ years building end-to-end analytical systems at the intersection of machine learning, growth analytics, and data engineering. In my current role at Auctane I own production ML systems on GCP (churn prediction, lead scoring, LTV modeling), lead an 11-person analytics team, and translate complex data into executive strategy that has influenced $5.6M+ in product revenue.

This portfolio spans NLP pipelines, ML modeling, agentic AI workflows, full-stack data apps, and cloud infrastructure — all built in Python, SQL, and GCP.

---

## Projects

### 🤖 Job Application Agent
*Multi-agent Claude Code pipeline for automated job applications*

A personal productivity system that chains 6 AI sub-agents (Job Analyst, Resume Expert, Fact Checker, Senior Editor, Cover Letter Writer, Doc Creator) to analyze a job posting, tailor a resume, generate a cover letter, produce submission-ready PDFs, and log everything to a SQLite tracker — all from a single slash command. Built to demonstrate practical multi-agent orchestration, not just theoretical AI tooling.

- **Technologies:** Claude Code Agent SDK, Python, WeasyPrint, Jinja2, SQLite, Google Drive MCP, Click
- **View Project:** [JobApplicationAgent](https://github.com/jrichwiltshire/Portfolio/tree/main/projects/JobApplicationAgent)

---

### 🏙️ Urban Mobility Discourse Analyzer
*NLP pipeline mining Reddit for walkability and transit sentiment*

Ingests posts from 5 subreddits via PRAW, applies BERTopic for topic modeling, VADER for sentiment scoring, and spaCy for city-entity extraction. Results feed a reactive Marimo dashboard with 5 analytical views: topic clustering (UMAP scatter), sentiment timelines, city comparison, and a post browser — all driven by global filter controls.

- **Technologies:** Python, BERTopic, sentence-transformers, VADER, spaCy, Marimo, Plotly, Pandas, Parquet
- **View Project:** [UrbanMobilityNLP](https://github.com/jrichwiltshire/Portfolio/tree/main/projects/UrbanMobilityNLP)

---

### 🎯 Job Search Aggregator & AI Matcher
*Async job-hunting engine with AI scoring and live dashboard*

Aggregates listings from 13+ sources (LinkedIn, Indeed, Y Combinator, and others), scores each posting against my resume using GPT-4o-mini, filters for high-signal matches, and delivers alerts to Discord. Runs on GitHub Actions with a client-side SQLite dashboard.

- **Technologies:** Python 3.13, Asyncio, httpx, OpenAI API, SQLite, GitHub Actions, SQL.js
- **View Project:** [JobSearchAggregator](https://github.com/jrichwiltshire/Portfolio/tree/main/projects/JobSearchAggregator)
- **Live Dashboard:** [View Job Dashboard](https://jrichwiltshire.github.io/Portfolio/dashboard.html)

---

### ✅ Task Management App
*Full-stack PWA with real-time Firestore sync*

A progressive web app built with Flet (Python UI framework) and Firebase. Features real-time bidirectional sync via Firestore `on_snapshot`, category-grouped shopping/task lists, and Google Calendar integration. Deployed on Railway.

- **Technologies:** Python, Flet, Firebase Admin SDK, Firestore, Google Calendar API, Railway
- **View Project:** [TaskManagementApp](https://github.com/jrichwiltshire/Portfolio/tree/main/projects/TaskManagementApp)

---

### 🚶 Walkability Prediction
*ML model for predicting urban walkability scores*

Predicts walkability scores from urban and environmental features using gradient boosting. Includes geospatial feature engineering, SHAP-based model explainability, and interactive Folium maps.

- **Technologies:** Python, XGBoost, scikit-learn, SHAP, GeoPandas, Folium, Pandas
- **View Project:** [WalkabilityPrediction](https://github.com/jrichwiltshire/Portfolio/tree/main/projects/WalkabilityPrediction)

---

### 🗺️ Interactive Travel Photo Map
*Geospatial photo visualization app*

Web app that plots travel photos on an interactive map with location metadata, clustering, and photo browsing. Built with Streamlit and Leaflet.js.

- **Technologies:** Python, Streamlit, Leaflet.js, SQL
- **View Project:** [TravelPhotoMap](https://github.com/jrichwiltshire/Portfolio/tree/main/projects/TravelPhotoMap)

---

## Skills

| Area | Tools |
|------|-------|
| **Languages** | Python (scikit-learn, Pandas, Polars, NumPy), SQL, LookML, HTML/CSS |
| **ML & NLP** | XGBoost, Logistic Regression, Gradient Boosting, KMeans, BERTopic, sentence-transformers, VADER, SHAP |
| **AI & Agents** | Claude Code Agent SDK, Claude MCP, OpenAI API, multi-agent orchestration |
| **Cloud & Infra** | GCP (BigQuery, Cloud Run, Pub/Sub, Vertex AI, Dataform), dbt, Docker, Firebase |
| **Data Viz** | Looker, Tableau, Plotly, Streamlit, Marimo |
| **Data Engineering** | ETL pipelines, data warehousing, dbt models, Airflow, data governance |

---

## Contact

- **Email:** jared.r.wiltshire@gmail.com
- **LinkedIn:** [jared-r-wiltshire-86757651](https://www.linkedin.com/in/jared-r-wiltshire-86757651/)
- **GitHub:** [jrichwiltshire](https://github.com/jrichwiltshire)
- **Resume:** [Jared R Wiltshire Resume](https://github.com/jrichwiltshire/Portfolio/blob/main/Jared%20R%20Wiltshire%20Resume.pdf)
