import sqlite3
import click
import os
from pathlib import Path

DB_PATH = os.getenv("TRACKER_DB_PATH", "job_tracker.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@click.group()
def cli():
    pass


@cli.command()
def init_db():
    """Create database tables."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'researching',
                job_url TEXT,
                date_applied DATE,
                date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recruiter_name TEXT,
                recruiter_email TEXT,
                recruiter_linkedin TEXT,
                notes TEXT,
                tailored_resume_path TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER REFERENCES applications(id),
                event_type TEXT,
                event_date TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    click.echo("Database initialized.")


@cli.command()
@click.option("--company", required=True)
@click.option("--role", required=True)
@click.option("--status", default="researching")
@click.option("--job-url", default=None)
@click.option("--resume-path", default=None)
def add(company, role, status, job_url, resume_path):
    """Add a new job application."""
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO applications (company, role, status, job_url, date_applied, tailored_resume_path)
               VALUES (?, ?, ?, ?, date('now'), ?)""",
            (company, role, status, job_url, resume_path),
        )
        click.echo(f"Added #{cur.lastrowid}: {company} — {role} [{status}]")


@cli.command()
@click.argument("app_id", type=int)
@click.option("--status", default=None)
@click.option("--notes", default=None)
@click.option("--recruiter-name", default=None)
@click.option("--recruiter-email", default=None)
@click.option("--recruiter-linkedin", default=None)
@click.option("--resume-path", default=None)
def update(app_id, status, notes, recruiter_name, recruiter_email, recruiter_linkedin, resume_path):
    """Update fields on an application."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        if not row:
            click.echo(f"No application #{app_id}.")
            return

        fields, values = [], []
        if status:
            fields.append("status=?"); values.append(status)
        if notes:
            existing = row["notes"] or ""
            combined = f"{existing}\n{notes}".strip()
            fields.append("notes=?"); values.append(combined)
        if recruiter_name:
            fields.append("recruiter_name=?"); values.append(recruiter_name)
        if recruiter_email:
            fields.append("recruiter_email=?"); values.append(recruiter_email)
        if recruiter_linkedin:
            fields.append("recruiter_linkedin=?"); values.append(recruiter_linkedin)
        if resume_path:
            fields.append("tailored_resume_path=?"); values.append(resume_path)

        if fields:
            fields.append("date_updated=CURRENT_TIMESTAMP")
            conn.execute(
                f"UPDATE applications SET {', '.join(fields)} WHERE id=?",
                values + [app_id],
            )
            click.echo(f"Updated #{app_id}.")


@cli.command("add-event")
@click.argument("app_id", type=int)
@click.option("--type", "event_type", required=True,
              type=click.Choice(["interview", "phone_screen", "follow_up", "deadline"]))
@click.option("--date", "event_date", required=True)
@click.option("--notes", default=None)
def add_event(app_id, event_type, event_date, notes):
    """Add an event (interview, follow-up, etc.) to an application."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO events (application_id, event_type, event_date, notes) VALUES (?,?,?,?)",
            (app_id, event_type, event_date, notes),
        )
        click.echo(f"Event added to #{app_id}: {event_type} on {event_date}")


@cli.command("list")
@click.option("--status", default=None)
def list_apps(status):
    """List applications, optionally filtered by status."""
    query = "SELECT id, company, role, status, date_applied FROM applications"
    params = []
    if status == "open":
        query += " WHERE status NOT IN ('rejected','withdrawn','offer')"
    elif status:
        query += " WHERE status=?"; params.append(status)
    query += " ORDER BY date_updated DESC"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        click.echo("No applications found.")
        return
    for r in rows:
        click.echo(f"#{r['id']:>3}  {r['company']:<25} {r['role']:<30} [{r['status']}]  {r['date_applied'] or ''}")


@cli.command()
@click.argument("app_id", type=int)
def show(app_id):
    """Show all details and events for an application."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        if not row:
            click.echo(f"No application #{app_id}.")
            return

        click.echo(f"\n{'='*60}")
        click.echo(f"#{row['id']}  {row['company']} — {row['role']}  [{row['status']}]")
        click.echo(f"Applied:   {row['date_applied'] or 'n/a'}")
        click.echo(f"Updated:   {row['date_updated']}")
        if row['job_url']:
            click.echo(f"Job URL:   {row['job_url']}")
        if row['tailored_resume_path']:
            click.echo(f"Resume:    {row['tailored_resume_path']}")
        if row['recruiter_name'] or row['recruiter_email']:
            click.echo(
                f"Recruiter: {row['recruiter_name'] or ''} "
                f"{row['recruiter_email'] or ''} "
                f"{row['recruiter_linkedin'] or ''}"
            )

        events = conn.execute(
            "SELECT event_type, event_date, notes FROM events WHERE application_id=? ORDER BY event_date",
            (app_id,),
        ).fetchall()
        if events:
            click.echo("\nEvents:")
            for e in events:
                line = f"  {e['event_date']}  {e['event_type']}"
                if e['notes']:
                    line += f"  — {e['notes']}"
                click.echo(line)

        if row['notes']:
            click.echo(f"\nNotes:\n{row['notes']}")
        click.echo()


if __name__ == "__main__":
    cli()
