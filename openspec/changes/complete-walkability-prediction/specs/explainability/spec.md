## ADDED Requirements

### Requirement: Compute SHAP values for trained model
The system SHALL compute SHAP values using `shap.TreeExplainer` on the trained XGBoost model and the full feature matrix.

#### Scenario: SHAP values computed without error
- **WHEN** the model is trained
- **THEN** `shap.TreeExplainer(model).shap_values(X)` runs successfully and returns an array of shape `(n_samples, n_features)`

### Requirement: Display SHAP summary plot
The system SHALL display a SHAP beeswarm summary plot showing global feature importance and direction of effect for all features.

#### Scenario: Summary plot rendered
- **WHEN** SHAP computation completes
- **THEN** a beeswarm plot is rendered showing all features ranked by mean |SHAP value|

### Requirement: Expose top/bottom neighborhoods with SHAP context
The system SHALL identify the top 5 and bottom 5 block groups by predicted walkability score and compute the dominant SHAP feature for each, making this data available for the AI chat context.

#### Scenario: Top/bottom neighborhoods identified
- **WHEN** SHAP analysis completes
- **THEN** a summary table is produced with block group GEOID, predicted score, and top contributing feature

#### Scenario: SHAP context string generated
- **WHEN** SHAP analysis completes
- **THEN** a compact plain-text string is generated summarizing: global feature importances (ranked), top 5 walkable neighborhoods, bottom 5 walkable neighborhoods — for injection into the Gemini system prompt
