---
name: job-track
description: 'Natural language job application tracker. Parses updates like "I got an interview at Stripe on Friday" or "Rejected by Google" and updates the SQLite tracker. Also handles interview prep lookups. Use when user says "/job-track" or gives natural language job application updates.'
allowed-tools: Bash
---

# Job Application Tracker

## Overview

Parse natural language job application updates and translate them to `tracker.py` CLI commands against the SQLite database.

## Workflow

### 1. Parse Intent

Read the user's input and classify into one of:

| Intent | Example |
|--------|---------|
| **add** | "Applying to Stripe for ML Engineer" |
| **status_update** | "Got rejected by Google", "Phone screen at Airbnb tomorrow" |
| **add_event** | "Interview at Stripe next Thursday 2pm", "Follow up with Netflix by Friday" |
| **add_note** | "Add note: HM is Sarah Chen, loved my NLP work" |
| **lookup** | "Show me my Stripe notes", "Pull up everything on the Amazon application" |
| **list** | "What applications do I have open?", "Show all active jobs" |

### 2. Find Matching Application (for updates/lookups)

```bash
cd projects/JobApplicationAgent && uv run python tracker.py list
```

Match the company name from the user's input against the list (fuzzy — "Stripe" matches "Stripe, Inc."). If ambiguous, show options and ask.

### 3. Execute the Right Command

**Add new application:**
```bash
uv run python tracker.py add --company "{company}" --role "{role}" [--job-url "{url}"] [--status researching]
```

**Update status:**
```bash
uv run python tracker.py update {id} --status {status}
```
Valid statuses: `researching`, `applied`, `phone_screen`, `interview`, `offer`, `rejected`, `withdrawn`

**Add event (interview/follow-up/deadline):**
```bash
uv run python tracker.py add-event {id} --type {interview|phone_screen|follow_up|deadline} --date "{ISO datetime}" [--notes "{notes}"]
```
Convert relative dates ("next Thursday", "tomorrow 2pm") to absolute ISO format using today's date (2026-05-02).

**Add note:**
```bash
uv run python tracker.py update {id} --notes "{new note text}"
```
Notes are appended, not replaced.

**Lookup / interview prep:**
```bash
uv run python tracker.py show {id}
```
Display all fields, events, and notes for the application.

**List all:**
```bash
uv run python tracker.py list [--status open]
```

### 4. Confirm to User

After running the command, echo back a concise confirmation:

```
Updated: Stripe / ML Engineer
  Status: phone_screen
  Event:  Interview — 2026-05-07 14:00
```

Or for a lookup:

```
Stripe — ML Engineer  [phone_screen]
Applied: 2026-04-28
Resume:  resumes/stripe-ml-engineer-2026-04-28.pdf

Events:
  2026-05-07 14:00  Interview

Notes:
  HM is Sarah Chen, liked my NLP work.
  Reached out via LinkedIn on 2026-04-29.
```

---

## Date Parsing Reference (today = 2026-05-02)

| User says | Resolves to |
|-----------|-------------|
| "tomorrow" | 2026-05-03 |
| "next Thursday" | 2026-05-07 |
| "Friday" | 2026-05-08 (next occurrence) |
| "May 15" | 2026-05-15 |
| "2pm" | append T14:00:00 to the resolved date |

---

## Notes

- If the user doesn't specify a time for an event, store date only (no time component).
- If tracker.py or the database doesn't exist yet, prompt: "Run `uv run python tracker.py init-db` first."
- Never delete applications — use status `withdrawn` instead.
