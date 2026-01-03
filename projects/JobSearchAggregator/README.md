# 🎯 Job Search Aggregator & AI Matcher

An automated, asynchronous job-hunting engine that aggregates listings from 13+ tech-focused sources, scores them against your resume using OpenAI, and delivers high-signal alerts to Discord.

## 🚀 Key Features

*   **13+ Job Sources:** Combines official APIs, RSS feeds, and scrapers to monitor the entire tech landscape.
*   **Asynchronous Engine:** Built with `httpx` and `asyncio` to query all sources in parallel, completing a full scan in seconds.
*   **AI Fit Scoring:** Every job is evaluated by `gpt-4o-mini` on a 1-10 scale against your local `resume.txt`.
*   **AI "Why Me?" Pitches:** For every match (7/10+), the AI generates a customized 3-bullet point pitch explaining why you are a fit.
*   **Salary Normalization:** Automatically converts hourly, monthly, and "k-suffixed" salaries into a standardized Annual USD format.
*   **Fuzzy Deduplication:** Smart logic prevents duplicate alerts for the same role across different platforms.
*   **Automated Pipeline:** Runs twice daily (9 AM / 5 PM) via GitHub Actions with automated database deployment to GitHub Pages.
*   **Live Dashboard:** A client-side SQL dashboard hosted on GitHub Pages for filtering and managing opportunities.

## 📡 Integrated Sources

1.  **Hacker News:** Latest "Who is Hiring" thread comments.
2.  **Y Combinator:** "Work at a Startup" official board.
3.  **Google Jobs:** Aggregator for LinkedIn, Indeed, and Glassdoor (via SearchApi).
4.  **RemoteOK:** Premium remote tech roles.
5.  **Remotive:** Hand-picked remote opportunities.
6.  **WeWorkRemotely:** The largest remote work community.
7.  **Jobspresso:** Curated remote roles in tech/marketing.
8.  **Built In Austin:** Regional tech focus for Austin, TX.
9.  **Adzuna:** Broad aggregator with structured salary data.
10. **Greenhouse:** Direct company boards (e.g., Stripe, Roblox).
11. **Lever:** Direct company boards (e.g., Anthropic, Netflix).
12. **Ashby:** Direct company boards (e.g., Notion, Vercel).
13. **Arbeitnow:** Modern tech job board.

## 🛠️ Tech Stack

*   **Language:** Python 3.13
*   **Async:** `asyncio`, `httpx`
*   **Database:** SQLite (persisted in `docs/`)
*   **AI:** OpenAI API (`gpt-4o-mini`)
*   **Orchestration:** GitHub Actions
*   **Frontend:** HTML5, `sql.js`, `water.css`

## ⚙️ Setup & Configuration

The project uses `uv` for dependency management.

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Environment Variables (.env):**
   ```env
   OPENAI_API_KEY=sk-...
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ADZUNA_APP_ID=...
   ADZUNA_APP_KEY=...
   SEARCHAPI_API_KEY=...
   ```

3. **Resume:**
   Place your professional summary/resume in `resume.txt` for the AI to use during scoring.

## 📈 Recent Updates

*   **Stability Patch:** Implemented a semaphore and safety delays to respect OpenAI's 3 RPM rate limit.
*   **Git Sync:** Added auto-rebase logic to GitHub Actions to prevent merge conflicts during automated DB updates.
*   **Google Jobs Integration:** Added a weekly deep-dive fetcher for LinkedIn/Indeed data via SearchApi.
*   **Schema Migration:** Added `why_me` support to the persistent storage layer.
