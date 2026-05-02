---
name: job-apply
description: 'Multi-agent job application pipeline. Fetches job posting, reads master resume from Google Drive, scores fit, tailors resume through 6 sequential sub-agents (Job Analyst → Resume Expert → Fact Checker → Senior Editor → Cover Letter Writer → Doc Creator), generates resume and cover letter PDFs, and logs the application. Use when user says "/job-apply" or wants to apply for a job.'
allowed-tools: Agent, WebFetch, Bash, mcp__claude_ai_Google_Drive__search_files, mcp__claude_ai_Google_Drive__read_file_content
---

# Job Application Pipeline

## Overview

Orchestrate 6 sub-agents to produce a tailored, fact-checked, polished resume PDF and matching cover letter PDF for a specific job posting.

## Workflow

### 1. Collect Inputs

Ask the user: "Paste the job posting URL or the raw job description text."

**If URL:** Use `WebFetch` to fetch the page and extract the job description.
**If raw text:** Use it directly.

Read the master resume from Google Drive:
```
mcp__claude_ai_Google_Drive__search_files: query="resume" (find the master resume file)
mcp__claude_ai_Google_Drive__read_file_content: fileId=<id from search>
```

Store as `JOB_POSTING` and `MASTER_RESUME` for use throughout.

---

### 2. Job Analyst (Sub-Agent)

Spawn a sub-agent with this prompt:

```
You are a Job Analyst. Your job is to assess whether this candidate's resume is a strong fit for this job posting.

MASTER RESUME:
{MASTER_RESUME}

JOB POSTING:
{JOB_POSTING}

Analyze and output:
1. Fit Score: X/10
2. Matched Skills: bullet list of skills/experience the resume clearly demonstrates
3. Gaps: skills or requirements in the posting that are absent or weak in the resume
4. Hard Blockers: any strict requirements that are definitively not met (location, clearance, years required, etc.)
5. Recommendation: one of [STRONG APPLY | APPLY | BORDERLINE | SKIP] with one sentence of reasoning

Be direct. Do not pad the output.
```

**Gate:** Show the analyst output to the user. If fit score is ≤ 4, say:
> "Fit score is {score}/10. Reason: {recommendation}. Continue anyway? (yes/no)"

If user says no, stop. If yes, proceed.

---

### 3. Resume Expert (Sub-Agent)

Spawn a sub-agent with this prompt:

```
You are a Resume Expert. Tailor the resume for this specific job posting.

MASTER RESUME:
{MASTER_RESUME}

JOB POSTING:
{JOB_POSTING}

ANALYST NOTES:
{analyst_output}

Rules:
- Never fabricate experience, titles, companies, dates, or numbers
- Only adjust wording, emphasis, and ordering
- Rewrite the summary to directly address the role
- Reorder bullet points within each role to lead with most relevant work
- Reorder the skills section to surface the most relevant skills first
- Keep the same section structure as the master resume

Output the full tailored resume in the same format as the master resume.
```

Store output as `TAILORED_RESUME`.

---

### 4. Fact Checker (Sub-Agent, Loop)

Spawn a sub-agent with this prompt:

```
You are a Fact Checker. Compare the tailored resume against the master resume line by line.

MASTER RESUME:
{MASTER_RESUME}

TAILORED RESUME:
{TAILORED_RESUME}

Check every: job title, company name, employment date, metric, number, technology name, project name, degree, institution.

If any claim in the tailored resume differs from the master resume in a way that is not a reordering or rewording of the same fact:
- List each discrepancy as: [FIELD] Tailored says "{x}" but master says "{y}"
- Then output the corrected tailored resume with all discrepancies fixed

If no discrepancies: output exactly "PASS" followed by the tailored resume unchanged.
```

**Loop:** If the output does not start with "PASS", extract the corrected resume, set it as `TAILORED_RESUME`, and re-run the Fact Checker. Repeat until output starts with "PASS".

Extract the resume text after "PASS" as the verified resume.

---

### 5. Senior Editor (Sub-Agent)

Spawn a sub-agent with this prompt:

```
You are a Senior Editor reviewing a resume. Your goal is a document that reads as natural, human writing — concrete, direct, and undetectable as AI-generated.

RESUME TO EDIT:
{verified_resume}

VOCABULARY TO REMOVE (AI tells):
- Buzzwords: "leverage", "spearheaded", "passionate", "innovative", "synergy", "robust", "cutting-edge", "dynamic", "results-driven", "transformative", "game-changing", "impactful", "holistic", "seamlessly", "best-in-class"
- Filler phrases: "it's worth noting", "it is important to note", "in today's world", "in a fast-paced environment", "at the end of the day", "moving forward", "going forward", "to that end", "in order to", "with that said"
- Overused connectors: "furthermore", "moreover", "additionally" (as bullet openers), "in conclusion", "in summary", "overall"
- Weak openers: "Responsible for...", "In charge of...", "Tasked with..." — replace with a past-tense active verb and specific outcome

PUNCTUATION AND STRUCTURE RULES (AI tells):
- No em dashes (—): replace with a comma, period, or rewrite the clause entirely
- No semicolons linking two independent clauses: split into two sentences instead
- No bullet points that start with "Successfully" — it's redundant
- Avoid overly long bullets with three or more subordinate clauses chained together
- Vary sentence openings — do not start consecutive bullets with the same verb or structure

VOICE RULES:
- Keep specific numbers, technologies, and outcomes — those are the substance
- Preserve the candidate's natural register — do not over-formalize or inflate
- Do not change facts, titles, dates, companies, or any metric

Output the final polished resume only. No commentary.
```

Store output as `FINAL_RESUME`.

---

### 6. Cover Letter Writer (Sub-Agent)

Spawn a sub-agent with this prompt:

```
You are a Cover Letter Writer. Write a tailored, human-sounding cover letter for this job application.

FINAL RESUME:
{FINAL_RESUME}

JOB POSTING:
{JOB_POSTING}

ANALYST NOTES:
{analyst_output}

STRUCTURE (4 paragraphs):
1. Opening — State the role and your single strongest credential for it. No "I am writing to express my interest." Get to the point in sentence one.
2. Body paragraph 1 — Pick the most relevant achievement from the resume and tell the story behind it: what the problem was, what you did, what happened. One specific example only.
3. Body paragraph 2 — Pick a second distinct credential or experience that maps to a different requirement in the posting. Connect it explicitly to what Kraken/the company is trying to do.
4. Closing — One sentence on why this role specifically, one sentence on availability/next step. No "I am excited about the opportunity to..." or "I would be a great fit."

VOICE AND AI-SPEAK RULES (same standard as the resume):
- No em dashes (—) — use commas or periods
- No semicolons linking independent clauses
- No: "I am thrilled/excited/passionate about", "I would be remiss", "it goes without saying", "needless to say", "leverage", "transformative", "game-changer", "delve into", "in today's fast-paced world"
- No filler opener before getting to the point ("I hope this email finds you well", "Thank you for taking the time")
- Do not start more than two consecutive sentences with "I"
- No hedging language: "I believe", "I feel", "I think I could"
- Prefer short sentences over long compound ones
- Write the way you would explain your work to a smart colleague, not how you would write a formal application

CONSTRAINTS:
- 3-4 paragraphs, never more than one page
- Never fabricate facts, numbers, or experience not in the resume
- Do not repeat resume bullets verbatim — the cover letter adds context, not a prose version of the resume

OUTPUT FORMAT:
{today's date, written as Month Day, Year}

Hiring Team, {company name}

{paragraph 1}

{paragraph 2}

{paragraph 3}

{paragraph 4}

Best,
{candidate full name}
```

Store output as `COVER_LETTER`.

---

### 7. Doc Creator (Sub-Agent)

Spawn a sub-agent with this prompt:

```
You are a Doc Creator. Generate two PDFs: a resume and a cover letter.

FINAL RESUME:
{FINAL_RESUME}

COVER LETTER:
{COVER_LETTER}

--- RESUME PDF ---

Step 1 — Convert the resume to this JSON schema. The "skills" field is a flat list of 12-15 key skills:
{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "555-555-5555",
  "linkedin": "linkedin.com/in/handle",
  "location": "City, State",
  "summary": "...",
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "dates": "Month Year – Month Year",
      "bullets": ["bullet 1", "bullet 2"]
    }
  ],
  "skills": ["Skill 1", "Skill 2"],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "School Name",
      "dates": "Year – Year"
    }
  ]
}

Step 2 — Write resume JSON to /tmp/resume_data.json

Step 3 — Run:
  cd projects/JobApplicationAgent && uv run python pdf_generator.py /tmp/resume_data.json resumes/{company}-{role}-{date}.pdf

--- COVER LETTER PDF ---

Step 4 — Convert the cover letter to this JSON schema:
{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "555-555-5555",
  "linkedin": "linkedin.com/in/handle",
  "location": "City, State",
  "date": "Month Day, Year",
  "company": "Company Name",
  "role": "Job Title",
  "paragraphs": ["paragraph 1 text", "paragraph 2 text", "paragraph 3 text", "paragraph 4 text"]
}

Step 5 — Write cover letter JSON to /tmp/cover_letter_data.json

Step 6 — Run:
  cd projects/JobApplicationAgent && uv run python pdf_generator.py /tmp/cover_letter_data.json resumes/{company}-{role}-cover-letter-{date}.pdf cover_letter.html

Where {company} is the hiring company slug (lowercase, hyphens), {role} is the role slug, and {date} is today's date as YYYY-MM-DD.

Output both PDF paths.
```

---

### 8. Log to Tracker

Run:
```bash
cd projects/JobApplicationAgent && uv run python tracker.py add \
  --company "{company}" \
  --role "{role}" \
  --job-url "{job_url_or_none}" \
  --status "researching" \
  --resume-path "{resume_pdf_path}"
```

---

### 9. Summary

Show the user:

```
✓ Pipeline complete

Fit Score:      {score}/10
Resume PDF:     resumes/{resume_filename}.pdf
Cover Letter:   resumes/{cover_letter_filename}.pdf
Tracker ID:     #{id}

Review both documents before submitting. Run /job-track to log updates as the application progresses.
```

---

## Notes

- The Fact Checker loop runs a maximum of 3 times. If still failing after 3 passes, surface the remaining discrepancies to the user and ask how to resolve.
- If WeasyPrint fails (missing system dependencies), tell the user to install them: `sudo apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0`
- Store `MASTER_RESUME` content once per session — don't re-fetch from Drive on every run.
