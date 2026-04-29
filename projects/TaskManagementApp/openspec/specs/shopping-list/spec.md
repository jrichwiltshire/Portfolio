## ADDED Requirements

### Requirement: Add item to shopping list
The system SHALL allow the user to add a new item by entering text and selecting a category from a predefined dropdown. The item SHALL be saved to Firestore and appear in the active list immediately.

#### Scenario: Successful item add
- **WHEN** the user enters item text and selects a category, then clicks Add
- **THEN** a new item document is created in Firestore with `checked: false` and appears in the active list under its category

#### Scenario: Empty input is ignored
- **WHEN** the user clicks Add with an empty text field
- **THEN** no item is created and no error is shown

### Requirement: Active items grouped by category
The system SHALL display all unchecked items grouped under their category heading, sorted alphabetically by category name.

#### Scenario: Items from multiple categories displayed
- **WHEN** the active list contains items from two or more categories
- **THEN** each category with items is shown as a heading with its items listed beneath it

#### Scenario: Empty categories not shown
- **WHEN** a category has no active items
- **THEN** that category heading does not appear in the active list

### Requirement: Check off an item
The system SHALL allow the user to check a checkbox next to any active item. Checked items SHALL move immediately to the completed section with struck-through text.

#### Scenario: Item checked
- **WHEN** the user checks the checkbox next to an active item
- **THEN** the item's `checked` field is set to `true` in Firestore, it disappears from the active list, and appears in the completed section with struck-through text

### Requirement: Uncheck a completed item
The system SHALL allow the user to uncheck a completed item, returning it to the active list under its original category.

#### Scenario: Item unchecked
- **WHEN** the user unchecks the checkbox next to a completed item
- **THEN** the item's `checked` field is set to `false` in Firestore and it moves back to the active list under its category

### Requirement: Delete individual completed item
The system SHALL allow the user to permanently delete a single completed item via a delete button shown next to each completed item.

#### Scenario: Single item deleted
- **WHEN** the user clicks the delete button next to a completed item
- **THEN** the item document is removed from Firestore and disappears from the completed section

### Requirement: Clear all completed items
The system SHALL provide a "Clear all" button in the completed section that deletes all completed items at once.

#### Scenario: Clear all clicked with completed items present
- **WHEN** the user clicks "Clear all" and completed items exist
- **THEN** all items with `checked: true` are deleted from Firestore and the completed section becomes empty

#### Scenario: Clear all clicked with no completed items
- **WHEN** the user clicks "Clear all" and there are no completed items
- **THEN** nothing happens

### Requirement: Predefined category list
The system SHALL use a fixed set of categories: Produce, Dairy & Eggs, Meat & Seafood, Bakery & Bread, Frozen, Pantry, Beverages, Snacks, Household, Personal Care, Other.

#### Scenario: Category dropdown displayed
- **WHEN** the user opens the category dropdown when adding an item
- **THEN** exactly the 11 predefined categories are shown as options
