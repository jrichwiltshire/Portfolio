from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sqlite3
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()


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


# --- 4. FETCHERS ---
def fetch_jobs_from_all_sources(search_keywords, city_filter, min_salary=0):
    print(f"Searching Arbeitnow for {search_keywords} in {city_filter}...")
    all_found_jobs = []

    # --- Source 1. Arbeitnow ---
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api")
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


def send_notification(job: JobListing):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL not found in environment.")
        return

    payload = {
        "content": f"🎯 **New {job.title} Role Found!**",
        "embeds": [
            {
                "title": f"{job.company} is hiring!",
                "description": f"📍 **Location:** {job.location}\n🔗 [Apply Here]({job.link})",
                "color": 5814783,
            }
        ],
    }
    requests.post(webhook_url, json=payload)


# --- 3. THE "WORKER" (MAIN EXECUTION) ---
if __name__ == "__main__":
    db = JobDatabase()

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

    # 2. Fetch real jobs
    real_jobs = fetch_jobs_from_all_sources(
        SETTINGS["keywords"], SETTINGS["city"], SETTINGS["min_salary"]
    )

    new_jobs_found = 0
    for job in real_jobs:
        # Check if it exists before trying to insert to track "newness"
        cursor = db.conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE external_id = ?", (job.external_id,))
        exists = cursor.fetchone()

        if not exists:
            db.upsert_job(job)
            send_notification(job)
            new_jobs_found += 1

    print(
        f"Check complete. Found {new_jobs_found} new matching jobs in {SETTINGS['city']}."
    )
