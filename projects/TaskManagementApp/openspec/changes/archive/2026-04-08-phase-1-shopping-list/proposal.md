## Why

The app needs a real-time, cross-device shopping list so items added on desktop are immediately visible on a phone (e.g., at a grocery store). This is the simplest, most immediately useful feature to build first and establishes the core sync infrastructure the rest of the app will depend on.

## What Changes

- Add a shopping list UI in Flet with add, check/uncheck, and delete functionality
- Persist shopping list items in Firebase Firestore with real-time sync via `on_snapshot`
- Group active items by category in the UI
- Move checked items to a completed section (struck through) with individual delete and "Clear all" bulk delete
- Replace the current skeleton `main.py` with a clean Flet app structure (clean slate)
- Fix the Firebase initialization bug in `firebase_config.py` (missing `initialize_app` call)
- Add Railway deployment configuration so the app is accessible via URL and installable as a PWA on Android

## Capabilities

### New Capabilities
- `shopping-list`: Add, check/uncheck, and delete shopping list items with predefined categories, real-time Firestore sync, and grouped display of active vs completed items
- `firebase-sync`: Firestore integration providing real-time multi-device sync via `on_snapshot` listeners; shared infrastructure for all future phases
- `pwa-deployment`: Railway deployment config + HTTPS enabling the Flet web app to be installed as a PWA on Android (Pixel 8)

### Modified Capabilities

## Impact

- `main.py`: Full rewrite (clean slate from skeleton)
- `firebase_config.py`: Fix missing `initialize_app` call; expose Firestore client
- New `shopping_list.py`: Shopping list view and Firestore listener logic
- New `Procfile` or `railway.toml`: Railway deployment config
- Dependencies: no new packages needed (flet, firebase-admin already present)
