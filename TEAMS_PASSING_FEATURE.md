# Per-Level Teams Passing Configuration - Feature Documentation

## Overview
Implemented configurable teams passing per level, allowing administrators to set different numbers of teams that can advance from each level to the next. This provides more flexibility in game design and progression.

## Problem Statement
Previously, the system had a single global setting (`teams_passing_per_level`) that applied to all levels. This meant the same number of teams would pass from Level 1 to Level 2, from Level 2 to Level 3, and so on. 

**Example of old limitation:**
- If set to 5 teams passing per level
- Level 1 → Level 2: 5 teams
- Level 2 → Level 3: 5 teams  
- Level 3 → Level 4: 5 teams

This didn't allow for progressive elimination or custom game flows.

## Solution
Added per-level configuration where each level can have its own `teams_passing` value.

**Example of new flexibility:**
- Level 1 → Level 2: 10 teams
- Level 2 → Level 3: 5 teams
- Level 3 → Level 4: 3 teams
- Level 4 (Final): 0 teams (no advancement)

## Changes Made

### 1. Database Model Update (`models.py`)
```python
class Level(db.Model):
    # ... existing fields ...
    teams_passing = db.Column(db.Integer, default=0)  # NEW FIELD
```

**Migration**: Created `migrate_teams_passing.py` to add the column to existing databases.

### 2. Game Initialization (`routes/admin.py`)
Updated `initialize_game` route to:
- Accept per-level teams passing configuration
- Create levels with individual `teams_passing` values
- Automatically set final level to 0 teams passing

### 3. Level Management (`routes/admin.py`)
Added `update_level_config` route to:
- Update `teams_passing` for individual levels after initialization
- Update level names
- Validate configuration

### 4. Initialize Game UI (`templates/admin/initialize_game.html`)
**Dynamic Form Generation:**
- JavaScript dynamically creates input fields for each level
- Shows visual cards for each level configuration
- Final level is marked and set to readonly (0 teams)
- Default value can be set and applied to all levels
- Real-time form generation as number of levels changes

**Features:**
- Visual distinction for final level (warning badge)
- Helpful hints for each level
- Form validation
- Responsive card layout

### 5. Manage Levels UI (`templates/admin/manage_levels.html`)
**Complete Redesign:**
- Card-based layout for each level
- Inline editing of teams_passing
- Visual status indicators (Active/Inactive/Final)
- Statistics display (questions count, teams passing)
- Summary table view
- Quick actions (Start/Stop, Manage Questions)

### 6. Dashboard Update (`templates/admin/dashboard.html`)
Added `teams_passing` column to level management table showing:
- Number of teams passing for regular levels
- "Final Level" badge for the last level

### 7. Database Migration (`migrate_teams_passing.py`)
Automated migration script that:
- Checks if column exists
- Adds `teams_passing` column if needed
- Populates existing levels with default values from `game_config`
- Sets final levels to 0

## User Interface

### Game Initialization Flow
1. Admin enters basic game configuration
2. Sets default teams passing value
3. System generates per-level configuration cards
4. Admin can customize each level's teams passing
5. Final level automatically set to 0
6. Submit to create game

### Level Management Flow
1. Admin navigates to Manage Levels
2. Sees card for each level with current configuration
3. Can edit teams_passing inline
4. Submit to update individual level
5. Changes reflected immediately

## Technical Details

### JavaScript Features
```javascript
// Dynamic form generation
function generateLevelConfig() {
    // Creates input fields for each level
    // Applies default values
    // Marks final level as readonly
}

// Auto-update when default changes
$('#teams_passing_per_level').on('change', function() {
    // Updates all level inputs with new default
});

// Form validation
$('#initGameForm').on('submit', function(e) {
    // Validates teams_passing values
});
```

### Database Schema
```sql
ALTER TABLE levels 
ADD COLUMN teams_passing INTEGER DEFAULT 0;

-- Update existing levels
UPDATE levels l 
JOIN game_config gc ON 1=1 
SET l.teams_passing = gc.teams_passing_per_level 
WHERE l.is_final = 0;

UPDATE levels 
SET teams_passing = 0 
WHERE is_final = 1;
```

## Backward Compatibility
- Existing `game_config.teams_passing_per_level` field retained
- Used as default value during initialization
- Existing databases can be migrated with provided script
- No breaking changes to existing functionality

## Benefits

### For Administrators
1. **Flexible Game Design**: Create progressive elimination games
2. **Custom Difficulty Curves**: Adjust competition intensity per level
3. **Easy Configuration**: Visual interface for each level
4. **Post-Init Editing**: Can modify teams passing after game creation

### For Game Flow
1. **Progressive Elimination**: Start with many teams, narrow down gradually
2. **Tournament Style**: Different advancement criteria per round
3. **Custom Scenarios**: 
   - Qualification rounds (many teams pass)
   - Semi-finals (fewer teams)
   - Finals (top teams only)

## Example Use Cases

### Tournament Style
```
Level 1 (Qualification): 20 teams → 10 teams pass
Level 2 (Quarter-finals): 10 teams → 4 teams pass
Level 3 (Semi-finals): 4 teams → 2 teams pass
Level 4 (Finals): 2 teams → Winner!
```

### Progressive Challenge
```
Level 1 (Easy): 15 teams → 12 teams pass (80%)
Level 2 (Medium): 12 teams → 8 teams pass (67%)
Level 3 (Hard): 8 teams → 4 teams pass (50%)
Level 4 (Expert): 4 teams → 2 teams pass (50%)
Level 5 (Final): 2 teams → Winner!
```

### Funnel Design
```
Level 1: 50 teams → 25 teams pass
Level 2: 25 teams → 10 teams pass
Level 3: 10 teams → 5 teams pass
Level 4: 5 teams → 3 teams pass
Level 5: 3 teams → Winner!
```

## Validation Rules

1. **Teams Passing ≥ 0**: Cannot be negative
2. **Final Level = 0**: Automatically set, readonly
3. **Required Field**: Must specify for each level
4. **Integer Values**: Only whole numbers accepted

## Files Modified

### New Files
- `migrate_teams_passing.py` - Database migration script

### Modified Files
- `models.py` - Added teams_passing field to Level model
- `routes/admin.py` - Updated initialization and added update route
- `templates/admin/initialize_game.html` - Dynamic per-level configuration
- `templates/admin/manage_levels.html` - Complete redesign with cards
- `templates/admin/dashboard.html` - Added teams_passing column

## Migration Instructions

### For New Installations
No migration needed - field is included in model.

### For Existing Installations
```bash
# Run migration script
uv run python migrate_teams_passing.py
```

The script will:
1. Check if migration is needed
2. Add teams_passing column
3. Populate with default values
4. Confirm success

## Future Enhancements

Potential improvements:
1. **Validation**: Ensure teams_passing doesn't exceed available teams
2. **Auto-calculation**: Suggest teams passing based on total teams
3. **Templates**: Pre-defined tournament structures
4. **Bulk Edit**: Update multiple levels at once
5. **History**: Track changes to teams_passing configuration
6. **Analytics**: Show actual vs. configured teams passing

## Testing Checklist

- [x] Database migration works on existing database
- [x] New game initialization with per-level config
- [x] Dynamic form generation works correctly
- [x] Final level set to 0 and readonly
- [x] Level configuration can be updated after init
- [x] Dashboard displays teams_passing correctly
- [x] Manage levels page shows all information
- [x] Form validation prevents invalid values
- [x] Backward compatibility maintained

## Conclusion

This feature provides administrators with fine-grained control over game progression, enabling more sophisticated and engaging treasure hunt experiences. The intuitive UI makes it easy to configure while maintaining backward compatibility with existing installations.

---

**Version**: 2.1.0  
**Date**: 2026-02-04  
**Status**: ✅ Complete and Tested
