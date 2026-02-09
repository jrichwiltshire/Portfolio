## Context
The goal is to set up a cross-platform task and note-taking application using Python and Flet. The app needs to support offline usage via SQLite and optional cloud sync with Firebase.

**Developer Preference:** The user prefers to write the implementation files themselves to learn. The assistant should provide code snippets and explanations in the chat rather than writing files directly, unless explicitly requested.

## Goals / Non-Goals
**Goals:**
- Initialize the Flet environment.
- Define the SQLite schema for tasks and notes.
- Implement the core UI layout: Markdown editor/preview and Shopping List.
- Integrate Google Calendar.

**Non-Goals:**
- Full implementation of all Firebase sync features (focus is on setup).
- Advanced styling or themes beyond the initial mockup.

## Decisions
- **Flet for UI:** Chosen for its ability to target web, desktop, and mobile from a single Python codebase.
- **SQLite for Local Storage:** Provides a robust, serverless database for offline-first capabilities.
- **Vertical Layout for Editor:** Maximizes screen space for both editing and previewing on desktop/tablet.

## Risks / Trade-offs
- [Risk] Performance of live Markdown rendering → [Mitigation] Throttling or debouncing updates if lag occurs.
- [Risk] Database migration issues → [Mitigation] Keep schema simple initially; use a basic versioning check.
