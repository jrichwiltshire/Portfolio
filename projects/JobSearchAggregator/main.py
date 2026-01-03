import asyncio
import sqlite3
import os
import json
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List
import logging

import httpx
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import openai

# --- CONFIGURATION ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "../../docs/job_aggregator.db"
RESUME_PATH = "resume.txt"

try:
    with open(RESUME_PATH, "r") as f:
        MY_RESUME = f.read()
except FileNotFoundError:
    MY_RESUME = ""
    logger.warning("resume.txt not found. AI scoring will be less accurate.")


# --- 1. DATA MODEL ---
@dataclass
class JobListing:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    link: str
    description: str
    posted_date: str
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    why_me: Optional[str] = None


# --- 2. DATABASE LOGIC ---
class JobDatabase:
    def __init__(self, db_name=DB_PATH):
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS jobs (
            external_id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            link TEXT,
            description TEXT,
            posted_date TEXT,
            min_salary INTEGER,
            max_salary INTEGER,
            applied INTEGER DEFAULT 0,
            why_me TEXT
        )
        """
        self.conn.execute(query)
        # Migration: Add column if it doesn't exist (for existing DBs)
        try:
            self.conn.execute("ALTER TABLE jobs ADD COLUMN why_me TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        self.conn.commit()

    def job_exists(self, external_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE external_id = ?", (external_id,))
        return cursor.fetchone() is not None

    def upsert_job(self, job: JobListing):
        """Inserts a job, or ignores it if the external_id already exists."""
        query = "INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.conn.execute(
            query,
            (
                job.external_id,
                job.source,
                job.title,
                job.company,
                job.location,
                job.link,
                job.description,
                job.posted_date,
                job.min_salary,
                job.max_salary,
                0,
                job.why_me,
            ),
        )
        self.conn.commit()


# --- 3. UTILITIES ---
def extract_salary(text):
    """
    Parses salary text to return (min_annual, max_annual).
    Handles: $120k, $120,000, $60/hr, $5000/mo.
    """
    if not text:
        return (None, None)

    text = text.lower().replace(",", "")

    # 1. Hourly check ($50-80/hr)
    hourly_matches = re.findall(r"\$(\d+)(?:-\$(\d+))?/hr", text)
    if hourly_matches:
        # Take the first match
        low, high = hourly_matches[0]
        min_sal = int(low) * 2080
        max_sal = int(high) * 2080 if high else min_sal
        return (min_sal, max_sal)

    # 2. 'k' suffix check ($120k - $150k)
    # Matches $120k or $120-150k
    k_matches = re.findall(r"\$(\d{2,3})k", text)
    if k_matches:
        nums = [int(m) * 1000 for m in k_matches]
        return (min(nums), max(nums))

    # 3. Standard check ($120000)
    # Look for large numbers
    std_matches = re.findall(r"\$(\d{4,7})", text)
    if std_matches:
        nums = [
            int(m) for m in std_matches if int(m) > 15000
        ]  # Filter out tiny numbers
        if nums:
            return (min(nums), max(nums))

    return (None, None)


async def calculate_fit_score(job: JobListing, resume_text: str):
    """Uses AI to compare the job to your resume."""
    if not resume_text:
        return {"score": 5, "reason": "No resume provided."}

    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    Role: Career Coach
    Task: Score this job fit (1-10) for the candidate.

    Resume: {resume_text[:2000]}...
    Job: {job.title} at {job.company}
    Desc: {job.description[:2000]}...

    Output JSON: {{ 
        "score": int, 
        "reason": "short string",
        "why_me": "3 bullet points (max 50 words) explaining why I am a good fit based on my resume. Use markdown bullets."
    }}
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return {"score": 0, "reason": "AI Error"}


def send_notification(job: JobListing, fit_data: dict):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    # Choose a color based on score: Green for 9-10, Yellow for 7-8
    color = 5025616 if fit_data["score"] >= 9 else 16776960

    base_url = "https://jrichwiltshire.github.io/Portfolio"
    apply_url = f"{base_url}?id={job.external_id}"

    payload = {
        "embeds": [
            {
                "title": f"🎯 Fit Score: {fit_data['score']}/10 - {job.title}",
                "url": job.link,
                "description": (
                    f"**Company:** {job.company}\n"
                    f"**Location:** {job.location}\n\n"
                    f"**AI Analysis:** {fit_data['reason']}\n\n"
                    f"**Why Me:**\n{fit_data.get('why_me', 'N/A')}\n\n"
                    f"📝 [Mark as Applied]({apply_url})"
                ),
                "color": color,
                "footer": {"text": f"Source: {job.source} | ID: {job.external_id}"},
            }
        ],
    }
    try:
        httpx.post(webhook_url, json=payload)
    except:
        pass


def is_duplicate(db, title, company):
    """Fuzzy check for duplicate roles within the last 7 days."""
    cursor = db.conn.cursor()

    # Remove special chars and lowercase for a 'fuzzy' match
    def clean(s):
        return re.sub(r"[^a-zA-Z0-9]", "", s).lower()

    cursor.execute(
        "SELECT title, company FROM jobs WHERE posted_date > date('now', '-7 days')"
    )
    for row in cursor.fetchall():
        if clean(title) == clean(row[0]) and clean(company) == clean(row[1]):
            return True
    return False


# --- 4. FETCHERS ---
# 0. Hacker News (API)
async def fetch_hacker_news(client, keywords):
    """Uses Algolia API to search the latest 'Who is Hiring' thread."""
    logger.info("Searching Hacker News...")
    url = "https://hn.algolia.com/api/v1/search?tags=story,author_whoishiring&hitsPerPage=1"
    jobs = []
    try:
        # 1. Find the latest thread
        res = await client.get(url)
        hits = res.json().get("hits", [])
        if not hits:
            return []
        thread_id = hits[0]["objectID"]

        # 2. Search comments for keywords (limit to first 3 to avoid spamming)
        search_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{thread_id}&query="
        for kw in keywords[:3]:
            resp = await client.get(search_url + kw)
            hits = resp.json().get("hits", [])
            for hit in hits:
                comment = hit.get("comment_text", "")
                sal_min, sal_max = extract_salary(comment)
                jobs.append(
                    JobListing(
                        source="HackerNews",
                        external_id=f"hn-{hit['objectID']}",
                        title=f"HN: {kw} Role",
                        company="HN Startup",
                        location="Remote/Hybrid",
                        link=f"https://news.ycombinator.com/item?id={hit['objectID']}",
                        description=comment,
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                        min_salary=sal_min,
                        max_salary=sal_max,
                    )
                )
    except Exception as e:
        logger.error(f"HN failed: {e}")
    return jobs


# 1. Arbeitnow (API)
async def fetch_arbeitnow(client, search_keywords):
    logger.info(f"Searching Arbeitnow for {search_keywords}...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    jobs = []

    # --- Source 1. Arbeitnow ---
    try:
        res = await client.get(url)
        data = res.json().get("data", [])
        for item in data:
            title = item["title"].lower()
            if any(k.lower() in title for k in search_keywords):
                sal_min, sal_max = extract_salary(item["description"])
                jobs.append(
                    JobListing(
                        source="Arbeitnow",
                        external_id=f"an-{item['slug']}",
                        title=item["title"],
                        company=item["company_name"],
                        location=item["location"],
                        link=item["url"],
                        description=item["description"],
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                        min_salary=sal_min,
                        max_salary=sal_max,
                    )
                )
    except Exception as e:
        logger.error(f"Error fetching from Arbeitnow: {e}")
    return jobs


# 2. RemoteOK (API)
async def fetch_remote_ok(client, keywords):
    """Fetcher for RemoteOK (Great for Data Science Roles)"""
    logger.info(f"Checking RemoteOK for {keywords}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36"
    }
    url = "https://remoteok.com/api"
    jobs = []

    try:
        res = await client.get(url, headers=headers)
        data = res.json()

        for item in data[1:]:
            title = item.get("position", "").lower()

            if any(k.lower() in title for k in keywords):
                sal_min, sal_max = extract_salary(item.get("description", ""))
                jobs.append(
                    JobListing(
                        source="RemoteOK",
                        external_id=f"rok-{item['id']}",
                        title=item.get("position"),
                        company=item.get("company", "Unknown"),
                        location="Remote",
                        link=item.get("url"),
                        description=item.get("description", ""),
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                        min_salary=sal_min,
                        max_salary=sal_max,
                    )
                )
    except Exception as e:
        logger.error(f"Error fetching from RemoteOK: {e}")
    return jobs


# 3. Remotive (API)
async def fetch_remotive(client, keywords):
    url = "https://remotive.com/api/remote-jobs"
    jobs = []
    try:
        res = await client.get(url)
        data = res.json().get("jobs", [])
        for item in data:
            if any(k.lower() in item["title"].lower() for k in keywords):
                jobs.append(
                    JobListing(
                        source="Remotive",
                        external_id=f"rm-{item['id']}",
                        title=item["title"],
                        company=item["company_name"],
                        location=item.get("candidate_required_location", "Remote"),
                        link=item["url"],
                        description=item["description"],
                        posted_date=item["publication_date"][:10],
                    )
                )
    except Exception as e:
        logger.error(f"Remotive failed: {e}")
    return jobs


# 4. WeWorkRemotely (RSS)
async def fetch_wwr(client, keywords):
    feeds = [
        "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
        "https://weworkremotely.com/categories/data-analysis.rss",
    ]
    jobs = []
    try:
        for feed_url in feeds:
            res = await client.get(feed_url)
            feed = feedparser.parse(res.text)
            for entry in feed.entries:
                if any(k.lower() in entry.title.lower() for k in keywords):
                    jobs.append(
                        JobListing(
                            source="WeWorkRemotely",
                            external_id=f"wwr-{entry.id}",
                            title=entry.title,
                            company=entry.get("author", "Unknown"),
                            location="Remote",
                            link=entry.link,
                            description=entry.summary,
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )
    except Exception as e:
        logger.error(f"WWR failed: {e}")
    return jobs


# 5. Jobspresso
async def fetch_jobespresso(client, keywords):
    url = "https://jobspresso.co/feed/"
    jobs = []
    try:
        res = await client.get(url)
        feed = feedparser.parse(res.text)
        for entry in feed.entries:
            if any(k.lower() in entry.title.lower() for k in keywords):
                jobs.append(
                    JobListing(
                        source="Jobspresso",
                        external_id=f"jp-{entry.id}",
                        title=entry.title,
                        company="Jobspresso Listing",
                        location="Remote",
                        link=entry.link,
                        description=entry.summary,
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                    )
                )
    except Exception as e:
        logger.error(f"Jobspresso failed: {e}")
    return jobs


# 6. Built In (Scraper) - Async
async def fetch_built_in_austin(client, keywords, city="austin"):
    """Fetcher for Built In Austin (Scraping/API hybrid approach)"""
    categories = ["data-analytics", "data-science"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    jobs = []

    for cat in categories:
        logger.info(f"Checking Built In Austin: {cat}...")
        url = f"https://www.builtinaustin.com/jobs/{cat}"

        try:
            res = await client.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "lxml")

            job_cards = soup.select('div[data-id="job-card"]')
            for card in job_cards:
                title_el = card.select_one("h2")
                company_el = card.select_one("div.company-name")
                link_el = card.select_one('a[data-id="job-card-title"]')

                if title_el and company_el and link_el:
                    title = title_el.text.strip()
                    if any(k.lower() in title.lower() for k in keywords):
                        link = "https://www.builtinaustin.com" + link_el["href"]
                        jobs.append(
                            JobListing(
                                source="BuiltInAustin",
                                external_id=f"bia-{hash(link)}",
                                title=title,
                                company=company_el.text.strip(),
                                location="Austin, TX",
                                link=link,
                                description="Visit link for full description...",
                                posted_date=datetime.now().strftime("%Y-%m-%d"),
                            )
                        )
        except Exception as e:
            logger.error(f"BuiltIn ({cat}) failed: {e}")
    return jobs


# 7. Adzuna (API)
async def fetch_adzuna(client, keywords):
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id:
        return []

    jobs = []
    query = "%20".join(keywords[:3])
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={app_id}&app_key={app_key}&results_per_page=20&what={query}&where=Austin"

    try:
        res = await client.get(url)
        data = res.json().get("results", [])
        for item in data:
            jobs.append(
                JobListing(
                    source="Adzuna",
                    external_id=f"adz-{item['id']}",
                    title=item["title"],
                    company=item["company"]["display_name"],
                    location=item["location"]["display_name"],
                    link=item["redirect_url"],
                    description=item["description"],
                    posted_date=item["created"][:10],
                    min_salary=item.get("salary_min"),
                    max_salary=item.get("salary_max"),
                )
            )
    except Exception as e:
        logger.error(f"Adzuna failed: {e}")
    return jobs


# 8. Greenhouse Boards (Direct)
async def fetch_greenhouse_companies(client, keywords, companies):
    """Fetcher for companies using Greenhouse (e.g., DoorDash, Stripe, etc.)"""
    jobs = []

    for co in companies:
        logger.info(f"Checking Greenhouse board for {co}...")
        url = f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs"
        try:
            res = await client.get(url)
            data = res.json().get("jobs", [])
            for item in data:
                title = item["title"]

                if any(k.lower() in title.lower() for k in keywords):
                    jobs.append(
                        JobListing(
                            source=f"Greehouse-{co}",
                            external_id=f"gh-{item['id']}",
                            title=title,
                            company=co.capitalize(),
                            location=item.get("location", {}).get("name", "Remote"),
                            link=item["absolute_url"],
                            description="View Greenhouse for details",
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )
        except:
            pass
    return jobs


# 9. Lever Boards (Direct Scraper)
async def fetch_lever(client, keywords, companies):
    jobs = []
    for co in companies:
        url = f"https://jobs.lever.co/{co}"
        try:
            res = await client.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            postings = soup.select(".posting")
            for post in postings:
                title = post.select_one("h5").text
                if any(k.lower() in title.lower() for k in keywords):
                    link = post.select_one("a.posting-title")["href"]
                    jobs.append(
                        JobListing(
                            source=f"Lever-{co}",
                            external_id=f"lev-{hash(link)}",
                            title=title,
                            company=co.capitalize(),
                            location="Remote/Hybrid",
                            link=link,
                            description="See Lever link",
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )
        except:
            pass
    return jobs


# 10. Ashby Boards (Direct API-ish)
async def fetch_ashby(client, keywords, companies):
    jobs = []
    for co in companies:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{co}"
        try:
            res = await client.get(url)
            data = res.json().get("jobs", [])
            for item in data:
                title = item["title"]
                if any(k.lower() in title.lower() for k in keywords):
                    jobs.append(
                        JobListing(
                            source=f"Ashby-{co}",
                            external_id=f"ash-{item['id']}",
                            title=title,
                            company=co.capitalize(),
                            location=item.get("location", "Remote"),
                            link=item["jobUrl"],
                            description="See Ashby Link",
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )

        except:
            pass
    return jobs


# 11. Y Combinator (Work at a Startup)
async def fetch_yc(client, keywords):
    """Queries YC's Work at a Startup board via their public Algolia API."""
    logger.info("Searching Y Combinator...")
    url = "https://zgob769v03-dsn.algolia.net/1/indexes/jobs_prod/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.13.1)%3B%20Browser&x-algolia-api-key=de064d669069600600000000000000&x-algolia-application-id=ZGOB769V03"
    jobs = []

    # We'll search for each keyword
    for kw in keywords[:3]:
        payload = {"query": kw, "hitsPerPage": 20, "filters": "jobType:full_time"}
        try:
            res = await client.post(url, json=payload)
            hits = res.json().get("hits", [])
            for hit in hits:
                jobs.append(
                    JobListing(
                        source="YC",
                        external_id=f"yc-{hit['id']}",
                        title=hit["title"],
                        company=hit["companyName"],
                        location=hit.get("location", "Remote/Hybrid"),
                        link=f"https://www.workatastartup.com/jobs/{hit['id']}",
                        description=hit.get("description", ""),
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                        min_salary=hit.get("minSalary"),
                        max_salary=hit.get("maxSalary"),
                    )
                )
        except Exception as e:
            logger.error(f"YC ({kw}) failed: {e}")
    return jobs


# 12. Google Jobs (via SearchApi - aggregates LinkedIn/Indeed)
async def fetch_google_jobs(client, keywords):
    api_key = os.getenv("SEARCHAPI_API_KEY")
    if not api_key:
        return []

    logger.info("Searching Google Jobs (LinkedIn/Indeed aggregator)...")
    jobs = []
    query = f"{keywords[0]} in Austin"
    url = f"https://www.searchapi.io/api/v1/search?engine=google_jobs&q={query}&api_key={api_key}"

    try:
        res = await client.get(url)
        results = res.json().get("jobs_results", [])
        for item in results:
            jobs.append(
                JobListing(
                    source=f"Google-{item.get('via', 'Search')}",
                    external_id=f"gj-{item['job_id']}",
                    title=item["title"],
                    company=item["company_name"],
                    location=item.get("location", "Unknown"),
                    link=(
                        item["related_links"][0]["link"]
                        if item.get("related_links")
                        else ""
                    ),
                    description=item.get("description", ""),
                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                )
            )
    except Exception as e:
        logger.error(f"Google Jobs failed: {e}")
    return jobs


# --- 3. MAIN ORCHESTRATOR
async def main():
    db = JobDatabase()
    # Limit to 3 concurrent AI calls to stay under rate limits
    ai_semaphore = asyncio.BoundedSemaphore(3)

    keywords = [
        "Data Analyst",
        "Data Scientist",
        "Analytics",
        "Machine Learning",
        "BI Developer",
    ]

    # Target Companies Lists
    gh_companies = [
        "crowdstrike",
        "cloudflare",
        "roblox",
        "atlassian",
        "spotify",
        "discord",
    ]
    lever_companies = ["linear", "anthropic", "netflix", "twitch"]
    ashby_companies = ["notion", "ramp", "incident", "vercel"]

    logger.info("Starting Async Job Search...")

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # Launch standard fetchers in parallel
        tasks = [
            fetch_hacker_news(client, keywords),
            fetch_yc(client, keywords),
            fetch_arbeitnow(client, keywords),
            fetch_remote_ok(client, keywords),
            fetch_remotive(client, keywords),
            fetch_wwr(client, keywords),
            fetch_jobespresso(client, keywords),
            fetch_built_in_austin(client, keywords),
            fetch_greenhouse_companies(client, keywords, gh_companies),
            fetch_lever(client, keywords, lever_companies),
            fetch_ashby(client, keywords, ashby_companies),
            fetch_adzuna(client, keywords),
        ]

        # Conditional task: Google Jobs (Run every 3 days to save SearchApi credits)
        # Check if day of year is divisible by 3
        if datetime.now().timetuple().tm_yday % 3 == 0:
            tasks.append(fetch_google_jobs(client, keywords))
        else:
            logger.info("Skipping Google Jobs today to save SearchAPI credits.")

        results = await asyncio.gather(*tasks)

    # Flatten list
    all_jobs = [job for sublist in results for job in sublist]
    logger.info(f"Fetched {len(all_jobs)} total jobs. Filtering & Scoring...")

    async def score_and_notify(job):
        if not db.job_exists(job.external_id) and not is_duplicate(
            db, job.title, job.company
        ):
            async with ai_semaphore:
                fit = await calculate_fit_score(job, MY_RESUME)
                if fit["score"] >= 7:
                    job.why_me = fit.get("why_me")  # Save the pitch
                    db.upsert_job(job)
                    send_notification(job, fit)
                    logger.info(f"MATCH: {job.title} ({fit['score']}/10)")
                    return True
        return False

    # Run scoring tasks in parallel (but throttled by semaphore)
    scoring_tasks = [score_and_notify(job) for job in all_jobs]
    results = await asyncio.gather(*scoring_tasks)
    new_count = sum(1 for r in results if r)

    logger.info(f"Done. Found {new_count} new relevant jobs.")


# --- 3. THE "WORKER" (MAIN EXECUTION) ---
if __name__ == "__main__":
    asyncio.run(main())
