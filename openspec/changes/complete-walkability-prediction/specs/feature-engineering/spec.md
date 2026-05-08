## ADDED Requirements

### Requirement: Compute OSMnx basic stats per block group
The system SHALL compute the following metrics for each block group using `ox.stats.basic_stats()` on the subgraph of edges intersecting that block group's polygon:
- `intersection_density_km`: intersections per sq km
- `street_density_km`: total street length per sq km
- `avg_street_length_m`: mean edge length in meters
- `streets_per_node_avg`: mean node degree (connectivity)
- `circuity_avg`: ratio of network distance to straight-line distance

#### Scenario: Stats computed for all block groups
- **WHEN** feature engineering runs
- **THEN** every block group in the study area has non-null values for all five basic stats

#### Scenario: Low circuity in grid neighborhoods
- **WHEN** a block group has a regular street grid
- **THEN** `circuity_avg` is close to 1.0 (network path ≈ straight-line distance)

### Requirement: Compute bearing entropy per block group
The system SHALL compute the Shannon entropy of the street bearing distribution for each block group, capturing how grid-like (low entropy) vs. organically laid out (high entropy) the street network is.

#### Scenario: Entropy distinguishes grid from organic
- **WHEN** two block groups are compared
- **THEN** a downtown grid block group has lower bearing entropy than a curved residential area

### Requirement: Compute network centrality and aggregate to block groups
The system SHALL compute approximate betweenness centrality and closeness centrality for all nodes in the full Austin walk graph (k=500 for betweenness), then spatially join nodes to block groups and aggregate (mean, max) per block group.

#### Scenario: Centrality uses full graph
- **WHEN** centrality is computed
- **THEN** it is run on the full 3km study-area graph, not on per-block-group subgraphs

#### Scenario: Centrality cached to disk
- **WHEN** centrality has been computed once
- **THEN** subsequent runs load from `cache/centrality.parquet` without recomputing

#### Scenario: All block groups have centrality values
- **WHEN** spatial join completes
- **THEN** block groups with no nodes are assigned 0 for centrality aggregates (not NaN)

### Requirement: Produce clean feature matrix
The system SHALL produce a final feature matrix with no NaN values, with one row per block group and columns for all engineered features plus the `NatWalkInd` target.

#### Scenario: No NaN in feature matrix
- **WHEN** the feature matrix is assembled
- **THEN** `df.isnull().sum().sum() == 0`
