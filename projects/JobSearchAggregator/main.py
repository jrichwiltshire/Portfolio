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
            max_salary INTEGER
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
        query = "INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
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

    prompt = f"""
    You are an expert career coach. Compare the following Resume and Job Description.

    Resume: {resume_text}
    Job Description: {job_description}

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
    print(f"Checking Built In Austin for {keywords}...")
    url = "https://www.builtinaustin.com/jobs/data-analytics"
    found_jobs = []

    try:
        res = requests.get(url)
        data = res.json()

        for item in data[1:]:  # data[0] is often a legal/disclaimer object, skip it
            title = item.get("position", "").lower()
            tags = [t.lower() for t in item.get("tags", [])]

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
                    external_id=f"bia-{item['id']}",
                    title=item["position"],
                    company=item["company"],
                    location="Austin",
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


def send_notification(job: JobListing, fit_data: dict):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    # Choose a color based on score: Green for 9-10, Yellow for 7-8
    color = 5025616 if fit_data["score"] >= 9 else 16776960

    payload = {
        "embeds": [
            {
                "title": f"🎯 Fit Score: {fit_data['score']}/10 - {job.title}",
                "url": job.link,
                "description": f"**Company:** {job.company}\n**Location:** {job.location}\n\n**AI Analysis:** {fit_data['reason']}",
                "color": color,
            }
        ],
    }
    requests.post(webhook_url, json=payload)


# --- 3. THE "WORKER" (MAIN EXECUTION) ---
if __name__ == "__main__":
    db = JobDatabase()

    fetchers = [
        fetch_arbeitnow,
        fetch_remote_ok,
        # fetch_built_in_austin
    ]

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
        "min_salary": 160000,
    }

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
