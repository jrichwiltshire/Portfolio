## ADDED Requirements

### Requirement: Render Folium choropleth of predicted walkability
The system SHALL render a Folium choropleth map showing predicted `NatWalkInd` scores by block group, using a red-yellow-green color scale, centered on the study area.

#### Scenario: Map renders with correct colors
- **WHEN** the map is displayed
- **THEN** block groups with higher predicted walkability appear greener and lower appear redder

#### Scenario: Map embedded in Marimo app
- **WHEN** running as `marimo run main.py`
- **THEN** the Folium map is rendered inline as an `mo.Html` component, not as a separate file

### Requirement: Tooltips show block group details
The system SHALL add Folium tooltips/popups to each block group showing: GEOID, predicted score, actual score, and top SHAP feature.

#### Scenario: Tooltip on hover
- **WHEN** user hovers over a block group on the map
- **THEN** a tooltip shows the block group's predicted walkability, actual walkability, and primary contributing feature

### Requirement: Toggle between predicted and actual walkability
The system SHALL provide two map layers (predicted vs. actual `NatWalkInd`) that the user can toggle using Folium's layer control.

#### Scenario: Layer toggle works
- **WHEN** user clicks the layer control
- **THEN** the map switches between predicted and actual walkability choropleths
