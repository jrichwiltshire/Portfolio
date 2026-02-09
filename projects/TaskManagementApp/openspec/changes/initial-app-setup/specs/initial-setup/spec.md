## ADDED Requirements

### Requirement: Flet Environment Setup
The application SHALL be initialized using the Flet framework to support cross-platform deployment.

#### Scenario: App Initialization
- **WHEN** the main application entry point is executed
- **THEN** a Flet window or mobile view is launched with the defined UI structure

### Requirement: SQLite Database Schema
The system SHALL use a local SQLite database to store tasks, notes, and shopping list items for offline access.

#### Scenario: Database Creation
- **WHEN** the application starts for the first time
- **THEN** the system creates a local SQLite database file with tables for tasks, notes, and list items

### Requirement: Markdown Editor and Preview
The application SHALL provide a vertical layout featuring a Markdown text editor and a real-time preview pane.

#### Scenario: Live Markdown Rendering
- **WHEN** the user types Markdown text into the editor
- **THEN** the preview pane updates immediately to display the rendered HTML/rich text

### Requirement: Shopping List View
The application SHALL include a dedicated view for managing shopping list items with checkable status.

#### Scenario: Toggle Item Completion
- **WHEN** the user clicks a checkbox next to a shopping list item
- **THEN** the item's status is updated in the database and reflected in the UI
