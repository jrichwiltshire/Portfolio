## ADDED Requirements

### Requirement: Railway deployment configuration
The system SHALL include a `Procfile` that starts the Flet app in web mode, binding to the port specified by the `$PORT` environment variable so Railway can route traffic correctly.

#### Scenario: App starts on Railway
- **WHEN** Railway runs the Procfile command
- **THEN** the Flet app starts and listens on the port provided by `$PORT`

### Requirement: HTTPS access via public URL
The deployed app SHALL be accessible via a public HTTPS URL provided by Railway (e.g., `https://yourapp.railway.app`) from both desktop browsers and mobile Chrome.

#### Scenario: Desktop access
- **WHEN** the user navigates to the Railway URL in a desktop browser
- **THEN** the Flet shopping list app loads and is fully functional

#### Scenario: Mobile access
- **WHEN** the user navigates to the Railway URL in Chrome on a Pixel 8
- **THEN** the Flet shopping list app loads and is fully functional

### Requirement: PWA installable on Android
The app SHALL be installable as a PWA from Chrome on Android. Chrome SHALL display an "Add to Home Screen" prompt when the user visits the app URL, resulting in a home screen icon that opens the app in standalone mode.

#### Scenario: PWA install prompt appears
- **WHEN** the user visits the app URL in Chrome on Pixel 8
- **THEN** Chrome shows an "Add to Home Screen" banner or install prompt

#### Scenario: Installed app opens standalone
- **WHEN** the user launches the app from the home screen icon
- **THEN** the app opens without browser navigation chrome (standalone mode)
