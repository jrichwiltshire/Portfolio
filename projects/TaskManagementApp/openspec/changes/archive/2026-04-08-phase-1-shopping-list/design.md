## Context

Starting from a clean slate. The existing `main.py` is a non-functional skeleton and will be replaced. The app is a personal-use Flet web app (no multi-user auth needed) that must sync in real-time between a desktop browser and a Pixel 8 Android device. Firebase Firestore is already configured (service account key present) but has a bug preventing initialization.

## Goals / Non-Goals

**Goals:**
- Functional shopping list with real-time Firestore sync
- Flet web app deployable to Railway and accessible via public HTTPS URL
- PWA-installable on Android via Chrome
- Clean, maintainable Flet app structure for future phases (tasks, notes, calendar)

**Non-Goals:**
- User authentication (personal use only; Firestore security rules lock to service account)
- Offline support (requires connectivity to sync)
- Multiple shopping lists
- Native Android APK (PWA via browser is sufficient for Phase 1)

## Decisions

### Flet server mode (not `flet publish`)
`flet publish` compiles Python to WebAssembly via Pyodide, enabling static hosting. However, `firebase-admin` uses native C extensions that don't run in Pyodide. Server mode (Python runs on Railway, browser connects via WebSocket) is the only viable path with the current Firebase Admin SDK.
- **Alternative considered**: Switching to Firebase REST API + Pyodide for static hosting. Rejected — adds complexity and loses the real-time `on_snapshot` listener pattern.

### Firebase Admin SDK for Firestore (no client-side Firebase)
The app runs as a single-user personal tool. Using the Admin SDK on the server means credentials never leave the server and there's no need for Firebase Authentication. Firestore security rules can be set to deny all public access.
- **Alternative considered**: Firebase JS SDK in browser. Rejected — user is Python-only and this would require JavaScript.

### `on_snapshot` for real-time sync
Firestore's `on_snapshot` listener pushes changes to the Flet server process immediately when data changes. The server then calls `page.update()` to refresh the UI for the connected session. This gives near-instant sync across devices without polling.

### Single `shopping_list.py` module
All shopping list logic (UI components, Firestore reads/writes, listener management) lives in one module. Keeps Phase 1 self-contained and easy to navigate for someone learning the codebase.

### Predefined categories (not free-form)
Reduces UI complexity (dropdown instead of text input for category). Categories cover common grocery needs; "Other" handles edge cases.

Categories: `Produce`, `Dairy & Eggs`, `Meat & Seafood`, `Bakery & Bread`, `Frozen`, `Pantry`, `Beverages`, `Snacks`, `Household`, `Personal Care`, `Other`

### Active items grouped by category; completed items flat list
Active items are grouped under category headers for easy scanning in a grocery store. Completed items are shown in a flat list (order doesn't matter once checked off) with struck-through text.

## Risks / Trade-offs

- [Risk] Flet WebSocket connection drops on mobile (screen lock, background) → Mitigation: Flet handles reconnection automatically; Firestore listener re-attaches on reconnect
- [Risk] Railway free tier may not exist long-term → Mitigation: App is containerizable; easy to migrate to any platform supporting Python
- [Risk] `on_snapshot` callback runs on a background thread; Flet UI updates must be thread-safe → Mitigation: Use `page.run_thread` or ensure `page.update()` calls are dispatched correctly per Flet docs

## Migration Plan

1. Fix `firebase_config.py` (add `initialize_app`)
2. Rewrite `main.py` as clean Flet app shell
3. Implement `shopping_list.py`
4. Add `Procfile` for Railway
5. Deploy to Railway; verify PWA install on Pixel 8
6. Set Firestore security rules to deny unauthenticated access

## Open Questions

- What port should Flet serve on for Railway? (Railway uses `$PORT` env var — Flet needs to respect this)
