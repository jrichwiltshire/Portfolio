## ADDED Requirements

### Requirement: Firebase app initialization
The system SHALL initialize the Firebase Admin SDK exactly once at application startup using a service account credentials file before any Firestore operations are performed.

#### Scenario: App starts successfully
- **WHEN** the Flet app starts
- **THEN** `firebase_admin.initialize_app` is called with valid credentials and no exception is raised

#### Scenario: Double initialization prevented
- **WHEN** the module is imported more than once in the same process
- **THEN** the app is not initialized a second time (checked via `firebase_admin._apps`)

### Requirement: Real-time shopping list sync
The system SHALL attach a Firestore `on_snapshot` listener to the shopping list collection on app load. Any change to the collection (add, update, delete) from any device SHALL trigger a UI refresh within 2 seconds under normal network conditions.

#### Scenario: Item added on another device
- **WHEN** a new item is written to Firestore from a second device
- **THEN** the `on_snapshot` callback fires and the Flet UI updates to show the new item without requiring a page refresh

#### Scenario: Item checked on another device
- **WHEN** an item's `checked` field is updated to `true` from a second device
- **THEN** the item moves from the active list to the completed section on all connected sessions

### Requirement: Firestore data schema
Each shopping list item SHALL be stored as a document in the `shopping_list/items` Firestore collection with the following fields: `text` (string), `checked` (boolean), `category` (string), `created_at` (timestamp).

#### Scenario: New item document structure
- **WHEN** a new item is added
- **THEN** the created Firestore document contains all four required fields with correct types
