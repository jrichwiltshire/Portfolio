## ADDED Requirements

### Requirement: Download OSM walk network
The system SHALL download the OpenStreetMap pedestrian walk network for a configurable center point and radius using OSMnx and cache the result to disk.

#### Scenario: First run downloads and caches
- **WHEN** no cached graph exists and the user runs the pipeline
- **THEN** the system downloads the OSM graph, saves it to `cache/`, and reports node/edge counts

#### Scenario: Subsequent runs use cache
- **WHEN** a cached graph file exists
- **THEN** the system loads from cache without making a network request

### Requirement: Download Census block groups
The system SHALL download Census block groups for Travis County (TX) using pygris and filter to those intersecting the study area.

#### Scenario: Block groups filtered to study area
- **WHEN** the pipeline runs
- **THEN** only block groups intersecting the 3km study circle are retained

### Requirement: Download EPA National Walkability Index
The system SHALL download the EPA National Walkability Index CSV from the official ZIP endpoint and extract `NatWalkInd` scores keyed by Census block group GEOID.

#### Scenario: ZIP contains nested CSV
- **WHEN** the EPA ZIP file is downloaded
- **THEN** the system finds the CSV at any nesting depth (not just root) and reads it successfully

#### Scenario: EPA data merged with block groups
- **WHEN** EPA data is loaded
- **THEN** it is merged onto the block group GeoDataFrame by GEOID, and block groups with no matching score are dropped

### Requirement: Cache slow operations
The system SHALL cache OSM graph downloads and EPA data to `cache/` so subsequent runs skip network requests.

#### Scenario: Cache hit skips download
- **WHEN** a cache file exists for a data source
- **THEN** the pipeline loads from disk and completes the data acquisition step in under 5 seconds
