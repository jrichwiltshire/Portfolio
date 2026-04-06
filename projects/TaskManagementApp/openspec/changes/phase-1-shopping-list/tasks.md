## 1. Firebase Setup

- [x] 1.1 Fix `firebase_config.py`: add `firebase_admin.initialize_app(cred)` call and guard against double initialization using `firebase_admin._apps`
- [x] 1.2 Expose the Firestore client (`firestore_db`) from `firebase_config.py` for use by other modules
- [x] 1.3 Verify Firebase connection works by writing and reading a test document manually

## 2. Shopping List Data Layer

- [x] 2.1 Create `shopping_list.py` with a function to add an item to Firestore (`text`, `checked: False`, `category`, `created_at`)
- [x] 2.2 Add a function to update an item's `checked` field in Firestore (used for both check and uncheck)
- [x] 2.3 Add a function to delete a single item document from Firestore by document ID
- [x] 2.4 Add a function to delete all documents where `checked == True` (bulk clear)
- [x] 2.5 Add an `on_snapshot` listener function that calls a provided callback whenever the collection changes

## 3. Shopping List UI

- [x] 3.1 Rewrite `main.py` as a clean Flet app shell (remove all skeleton code); call `shopping_list` view from `main`
- [x] 3.2 Build the add-item bar: `ft.TextField` for item text + `ft.Dropdown` with 11 predefined categories + Add button
- [x] 3.3 Build the active items section: render items grouped by category with a `ft.Checkbox` per item; checking an item calls the Firestore update function
- [x] 3.4 Build the completed section: render checked items as struck-through text with an individual delete button per item and a "Clear all" button
- [x] 3.5 Wire the `on_snapshot` listener to re-render both sections on any Firestore change; ensure `page.update()` is called correctly from the background thread
- [x] 3.6 Ensure empty input in the add bar is ignored (no Firestore write)

## 4. Deployment

- [ ] 4.1 Add a `Procfile` with the command to start Flet in web mode on `$PORT`
- [ ] 4.2 Push code to GitHub and connect the repo to Railway
- [ ] 4.3 Add `firebase_service_account_key.json` as a Railway environment secret (do not commit the key to git — confirm it is in `.gitignore`)
- [ ] 4.4 Verify the app loads at the Railway HTTPS URL from a desktop browser
- [ ] 4.5 Open the Railway URL in Chrome on Pixel 8 and confirm the PWA "Add to Home Screen" prompt appears
- [ ] 4.6 Install the PWA and verify it opens in standalone mode and syncs with desktop in real-time
