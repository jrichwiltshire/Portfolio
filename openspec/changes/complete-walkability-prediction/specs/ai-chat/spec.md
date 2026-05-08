## ADDED Requirements

### Requirement: Load Gemini API key from environment
The system SHALL load the Gemini API key from a `.env` file using `python-dotenv` and SHALL NOT accept hardcoded credentials in source code.

#### Scenario: Key loaded from .env
- **WHEN** the app starts
- **THEN** `GEMINI_API_KEY` is read from `.env` via `dotenv.load_dotenv()` before any Gemini client is initialized

#### Scenario: Missing key produces clear error
- **WHEN** `GEMINI_API_KEY` is not set
- **THEN** the app raises a descriptive error rather than failing with an obscure API exception

### Requirement: Inject model context into Gemini system prompt
The system SHALL construct a Gemini system prompt that includes: the study area description, global SHAP feature importances, and the top 5 / bottom 5 neighborhoods by predicted walkability score.

#### Scenario: System prompt contains SHAP context
- **WHEN** the chat is initialized
- **THEN** the Gemini system prompt includes ranked feature importances and neighborhood examples derived from the trained model

### Requirement: Provide conversational chat interface in Marimo
The system SHALL render a chat UI in the Marimo app using `mo.ui.chat` (or equivalent) backed by the Gemini API, allowing users to ask questions about the model results.

#### Scenario: User asks about feature importance
- **WHEN** user asks "what is the most important factor for walkability?"
- **THEN** Gemini responds with an answer grounded in the SHAP context (e.g., referencing intersection density or circuity)

#### Scenario: User asks about a specific neighborhood
- **WHEN** user asks "why is [neighborhood] walkable?"
- **THEN** Gemini responds referencing the top SHAP features for that area from the baked-in context

### Requirement: Multi-turn conversation
The system SHALL maintain conversation history across turns so users can ask follow-up questions without re-explaining context.

#### Scenario: Follow-up question understood
- **WHEN** user asks "what about the least walkable one?" after asking about the most walkable
- **THEN** Gemini correctly interprets "the least walkable one" from conversation history
