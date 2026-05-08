## ADDED Requirements

### Requirement: Train XGBoost regression model
The system SHALL train an XGBoost regression model to predict `NatWalkInd` from the engineered network features, using 5-fold cross-validation to evaluate performance given the small dataset (~766 samples).

#### Scenario: Model trains without error
- **WHEN** the feature matrix is complete
- **THEN** an XGBoost regressor fits successfully and cross-validation scores are reported

#### Scenario: CV metrics reported
- **WHEN** training completes
- **THEN** mean and std of RMSE and R² across 5 folds are printed/displayed

### Requirement: Generate out-of-sample predictions for all block groups
The system SHALL generate predicted `NatWalkInd` scores for all block groups (using cross-validated out-of-fold predictions) and attach them to the GeoDataFrame for visualization.

#### Scenario: All block groups have a prediction
- **WHEN** prediction step completes
- **THEN** the block group GeoDataFrame has a `predicted_walkability` column with no nulls

### Requirement: Report model performance summary
The system SHALL display a brief performance summary including overall RMSE, R², and a residual scatter plot (actual vs. predicted).

#### Scenario: Residual plot displayed
- **WHEN** model evaluation runs
- **THEN** a matplotlib scatter plot of actual vs. predicted walkability scores is shown with an identity line
