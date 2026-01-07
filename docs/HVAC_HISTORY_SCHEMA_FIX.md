# HVAC History Schema Fix

## Problem Identified

The history page displayed two sections (Settings and HVAC) with **inconsistent and duplicative data**:

### Original Issues:
1. **HVAC History** table only stored ONE target temperature:
   - Stored `target_temp` based on current mode (heat OR cool)
   - Lost information about the other setpoint
   - In `auto` mode, only one target was visible
   - No fan_mode information stored

2. **Settings History** tracked changes separately:
   - Stored `target_temp_heat` and `target_temp_cool` individually
   - Complete but disconnected from HVAC state

3. **Result**: Incomplete, inconsistent data across two tables

## Solution Implemented

Updated HVAC history to store **complete state** information:

### Schema Changes
**Old Schema:**
```sql
CREATE TABLE hvac_history (
    system_temp REAL,
    target_temp REAL,          -- Only one setpoint!
    hvac_mode TEXT,
    heat_active INTEGER,
    cool_active INTEGER,
    fan_active INTEGER,
    heat2_active INTEGER,
    timestamp TIMESTAMP
)
```

**New Schema:**
```sql
CREATE TABLE hvac_history (
    system_temp REAL,
    target_temp_heat REAL,     -- ✓ Heating setpoint
    target_temp_cool REAL,     -- ✓ Cooling setpoint
    hvac_mode TEXT,
    fan_mode TEXT,             -- ✓ Fan mode (auto/on)
    heat_active INTEGER,
    cool_active INTEGER,
    fan_active INTEGER,
    heat2_active INTEGER,
    timestamp TIMESTAMP
)
```

### Code Changes

1. **[database.py](src/database.py)**
   - Updated `log_hvac_state()` signature to accept both target temps and fan_mode
   - Added `_migrate_schema()` method for automatic migration
   - Schema now matches Settings table structure

2. **[thermostat.py](src/thermostat.py)**
   - Updated `_log_hvac_history()` to pass complete state
   - Logs both `target_temp_heat` and `target_temp_cool` always

3. **[web_interface.py](src/web_interface.py)**
   - Updated `/api/history/hvac` to convert both temperatures
   - Handles legacy `target_temp` field for backward compatibility

4. **[history.html](src/templates/history.html)**
   - Updated HVAC table to show both heat and cool targets
   - Added fan_mode column
   - JavaScript handles both new and legacy data formats

5. **Unit Tests**
   - Updated all test cases with new signature
   - Added assertions for new fields

## Migration

### Automatic Migration
The database automatically migrates when initialized:
- Detects old schema
- Creates new table structure
- Migrates existing data:
  - For `heat` mode: maps `target_temp` → `target_temp_heat`
  - For `cool` mode: maps `target_temp` → `target_temp_cool`
  - For `auto` mode: maps `target_temp` to both
  - Sets default `fan_mode = 'auto'` for legacy records
- Preserves all timestamps and IDs

### Manual Migration
For manual migration or troubleshooting:
```bash
# Back up database first!
cp thermostat.db thermostat.db.backup

# Run migration script
python migrate_hvac_history.py thermostat.db
```

## Benefits

1. **Complete HVAC State**: Every log entry shows full system configuration
2. **Consistency**: HVAC history now matches settings structure
3. **Auto Mode Support**: Both heat and cool setpoints visible
4. **Better Analysis**: Can see how both setpoints change over time
5. **No Data Loss**: Migration preserves all existing history
6. **Backward Compatible**: Code handles both old and new formats

## History Page Display

### Before:
```
Time        | System | Target | Mode | Heat | Cool | Fan
12:00 PM    | 72.0°F | 68.0°F | HEAT | ON   | OFF  | ON
```

### After:
```
Time        | System | Heat Target | Cool Target | Mode | Fan Mode | Heat | Cool | Fan
12:00 PM    | 72.0°F | 68.0°F      | 75.0°F      | HEAT | AUTO     | ON   | OFF  | ON
```

## Testing

Run unit tests to verify:
```bash
# Test database migrations
python -m pytest tests/unit/test_database_unit.py::TestDatabasePersistence::test_log_hvac_state -v

# Test web interface
python -m pytest tests/unit/test_web_interface_unit.py::TestAPIRoutes -v

# Run all tests
python -m pytest tests/unit/ -v
```

## Files Modified

- ✓ `src/database.py` - Schema and logging
- ✓ `src/thermostat.py` - State logging
- ✓ `src/web_interface.py` - API conversion
- ✓ `src/templates/history.html` - Display updates
- ✓ `tests/unit/test_database_unit.py` - Updated tests
- ✓ `tests/unit/test_web_interface_unit.py` - Updated tests

## Files Created

- ✓ `migrate_hvac_history.py` - Standalone migration script
- ✓ `docs/HVAC_HISTORY_SCHEMA_FIX.md` - This documentation

## Deployment

1. **Test Environment**: Deploy and verify migration works
2. **Backup**: Always back up `thermostat.db` before updating
3. **Update**: Deploy new code (migration runs automatically)
4. **Verify**: Check history page displays both temperatures
5. **Monitor**: Watch logs for migration success message

## Rollback

If issues occur:
1. Stop thermostat service
2. Restore database backup: `cp thermostat.db.backup thermostat.db`
3. Revert to previous code version
4. Restart service

## Future Enhancements

Potential improvements:
- Add graphing of both setpoints over time
- Show deadband (cool - heat) in auto mode
- Highlight when setpoints change via schedule vs manual
- Export HVAC history to CSV with all fields
