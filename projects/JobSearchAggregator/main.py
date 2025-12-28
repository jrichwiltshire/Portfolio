from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sqlite3
import requests
import re
import os
import openai
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

with open("resume.txt", "r") as f:
    MY_RESUME = f.read()


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
    posted_date: datetime
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None


# --- 2. DATABASE LOGIC ---
class JobDatabase:
    def __init__(self, db_name="job_aggregator.db"):
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
            applied INTEGER DEFAULT 0 -- 0 = No, 1 = Yes
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def job_exists(self, external_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE external_id = ?", (external_id,))
        return cursor.fetchone() is not None

    def upsert_job(self, job: JobListing):
        """Inserts a job, or ignores it if the external_id already exists."""
        query = "INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
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
            ),
        )
        self.conn.commit()


# --- 3. UTILITIES ---
def extract_salary(description):
    """Simple regex to find salary numbers like $120,000 in text."""
    # Matches patterns like $100,000 or $100k
    matches = re.findall(r"\$(\d{1,3}(?:,\d{3})*)", description)
    if matches:
        # Clean the string and convert to integer
        nums = [
            int(m.replace(",", "")) for m in matches if int(m.replace(",", "")) > 1000
        ]
        return min(nums) if nums else None
    return None


def calculate_fit_score(job_description, resume_text):
    """Uses AI to compare the job to your resume."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    truncated_desc = (
        job_description[:12000] if job_description else "No description provided."
    )

    prompt = f"""
    You are an expert career coach. Compare the following Resume and Job Description.

    Resume: {resume_text}
    Job Description: {truncated_desc}

    Return ONLY a JSON object with:
    1. "score": An integer from 1 to 10.
    2. "reason": A one-sentence explanation of why it fits or doesn't.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Scoring Error: {e}")
        return None


def send_notification(job: JobListing, fit_data: dict):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

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
                    f"📝 [Mark as Applied]({apply_url})"
                ),
                "color": color,
                "footer": {"text": f"Source: {job.source} | ID: {job.external_id}"},
            }
        ],
    }
    requests.post(webhook_url, json=payload)


def optimize_search_queries(db_path="job_aggregator.db"):
    """Analyzes high-scoring jobs to suggest better search terms."""
    conn = sqlite3.connect(db_path)
    # Get title of jobs that had high match scores in previous runs
    cursor = conn.execute(
        "SELECT title FROM jobs WHERE applied = 1 OR description LIKE '%Score: 9%' LIMIT 10"
    )
    past_titles = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not past_titles:
        return [
            "Data Analyst",
            "Data Scientist",
            "Analytics",
            "Machine Learning",
            "BI Developer",
        ]

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
    Based on these job titles I liked: {past_titles}
    Identify the top 5 most effective 'Search Keywords' I should use on job boards to find simliar high-paying roles in Austin.
    Return ONLY a JSON list of strings.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        new_keywords = json.loads(response.choices[0].message.content).get(
            "keywords", []
        )
        return new_keywords
    except:
        return [
            "Data Analyst",
            "Data Scientist",
            "Analytics",
            "Machine Learning",
            "BI Developer",
        ]


# --- 4. FETCHERS ---
def fetch_arbeitnow(search_keywords, city_filter, min_salary=0):
    print(f"Searching Arbeitnow for {search_keywords} in {city_filter}...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    all_found_jobs = []

    # --- Source 1. Arbeitnow ---
    try:
        res = requests.get(url)
        data = res.json().get("data", [])
        for item in data:
            title = item["title"].lower()
            location = item["location"].lower()

            if (
                any(k.lower() in title for k in search_keywords)
                and city_filter.lower() in location
            ):
                desc = item["description"]
                detected_salary = extract_salary(desc)

                if detected_salary and detected_salary < min_salary:
                    continue

                job = JobListing(
                    source="Arbeitnow",
                    external_id=f"an-{item['slug']}",  # Creating a unique ID
                    title=item["title"],
                    company=item["company_name"],
                    location=item["location"],
                    link=item["url"],
                    description=item["description"],
                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                    min_salary=None,
                    max_salary=None,
                )
                all_found_jobs.append(job)
    except Exception as e:
        print(f"Error fetching from Arbeitnow: {e}")

    return all_found_jobs


def fetch_built_in_austin(keywords, city_filter, min_salary=0):
    """Fetcher for Built In Austin (Scraping/API hybrid approach)"""
    categories = ["data-analytics", "data-science"]
    headers = {"User-Agent": "Mozilla/5.0"}
    found_jobs = []

    for cat in categories:
        print(f"Checking Built In Austin: {cat}...")
        url = f"https://www.builtinaustin.com/jobs/{cat}"

        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")

            job_cards = soup.find_all("div", {"data-id": "job-card"})
            for card in job_cards:
                title_el = card.find("h2")
                company_el = card.find("div", {"class": "company-name"})

                # Check if elements were found
                if title_el and company_el:
                    title = title_el.text.strip()
                    company = company_el.text.strip()
                    if any(k.lower() in title.lower() for k in keywords):
                        company = card.find(
                            "div", {"class": "company-name"}
                        ).text.strip()
                        link = "https://www.builtinaustin.com" + card.find("a")["href"]

                        job = JobListing(
                            source="BuiltInAustin",
                            external_id=f"bia-{hash(link)}",
                            title=title,
                            company=company,
                            location="Austin, TX",
                            link=link,
                            description="Visit link for full description...",
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                        )
                        found_jobs.append(job)
        except Exception as e:
            print(f"Error fetching from BuiltInAustin: {e}")
    return found_jobs


def fetch_remote_ok(keywords, city_filter, min_salary=0):
    """Fetcher for RemoteOK (Great for Data Science Roles)"""
    print(f"Checking RemoteOK for {keywords}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36"
    }
    url = "https://remoteok.com/api"
    found_jobs = []

    try:
        res = requests.get(url, headers=headers)
        data = res.json()

        for item in data[1:]:  # data[0] is often a legal/disclaimer object, skip it
            title = item.get("position", "").lower()

            if any(k.lower() in title for k in keywords):
                # Salary check
                salary = item.get("salary_min") or extract_salary(
                    item.get("description", "")
                )
                if salary and salary < min_salary:
                    continue

                job = JobListing(
                    source="RemoteOK",
                    external_id=f"rok-{item['id']}",
                    title=item["position"],
                    company=item["company"],
                    location="Remote",
                    link=item["url"],
                    description=item["description"],
                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                    min_salary=salary,
                    max_salary=item.get("salary_max"),
                )
                found_jobs.append(job)
    except Exception as e:
        print(f"Error fetching from RemoteOK: {e}")
    return found_jobs


def fetch_greenhouse_companies(keywords, city_filter, min_salary=0):
    """Fetcher for companies using Greenhouse (e.g., DoorDash, Stripe, etc.)"""
    target_companies = ["doordash", "stripe", "canva", "crunchyroll"]
    found_jobs = []

    for co in target_companies:
        print(f"Checking Greenhouse board for {co}...")
        url = f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs"
        try:
            res = requests.get(url).json()
            for item in res.get("jobs", []):
                title = item["title"].lower()
                location = item.get("location", {}).get("name", "").lower()

                if (
                    any(k.lower() in title for k in keywords)
                    and city_filter.lower() in location
                ):
                    job = JobListing(
                        source=f"Greehouse-{co}",
                        external_id=f"gh-{item['id']}",
                        title=item["title"],
                        company=co.capitalize(),
                        location=item.get("location", {}).get("name"),
                        link=item["absolute_url"],
                        description="View Greenhouse for details",
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                    )
                    found_jobs.append(job)
        except:
            continue
    return found_jobs


# --- 3. THE "WORKER" (MAIN EXECUTION) ---
if __name__ == "__main__":
    db = JobDatabase()

    fetchers = [
        fetch_arbeitnow,
        fetch_remote_ok,
        fetch_built_in_austin,
        fetch_greenhouse_companies,
    ]

    optimized_keywords = optimize_search_queries()

    # 1. Define focus areas
    SETTINGS = {
        "keywords": [
            "Data Analyst",
            "Data Scientist",
            "Analytics",
            "Machine Learning",
            "BI Developer",
        ],
        "city": "Austin",
        "min_salary": 0,
    }

    SETTINGS["keywords"] = list(set(SETTINGS["keywords"] + optimized_keywords))

    new_jobs_found = 0
    for fetch_func in fetchers:
        try:
            real_jobs = fetch_func(
                SETTINGS["keywords"], SETTINGS["city"], SETTINGS["min_salary"]
            )

            for job in real_jobs:
                if not db.job_exists(job.external_id):
                    ai_evaluation = calculate_fit_score(job.description, MY_RESUME)

                    if ai_evaluation and ai_evaluation.get("score", 0) >= 7:
                        db.upsert_job(job)
                        send_notification(job, ai_evaluation)
                        new_jobs_found += 1

        except Exception as e:
            print(f"Error in {fetch_func.__name__}: {e}")
    print(
        f"Check complete. Found {new_jobs_found} new matching jobs in {SETTINGS['city']}."
    )
