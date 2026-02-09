# Unified Task & Notes App

**Core Goal:** A Python-based app that works on both Windows (PC) and Mobile.

**Key Features:*
1. Markdown-based note taking.
2. Shopping/To-do lists (Keep-style).
3. Integration with Google Calendar for events.

**Technology Stack:*
- **Backend:** Python
- **Frontend:** Flet (Cross-platform GUI framework)
- **Sync Method:** Local file storage with periodic cloud synchronization (e.g., Firebase)

### UI Requirements

1. **Markdown Previewer**:
   - Use `ft.TextField(multiline=True)` for the Markdown Editor.
   - Use `ft.Markdown()` for the Preview Pane to render live.

2. **Shopping List View**:
