# Multi-Stage HVAC Support

## Overview

The thermostat now supports **N+1 configurable heating and cooling stages**, allowing you to control complex HVAC systems with multiple stages of heating/cooling capacity. This is ideal for:

- **Multi-stage heat pumps** (stage 1, stage 2, emergency heat)
- **Dual-fuel systems** (heat pump + gas furnace backup)
- **Multi-speed compressors**
- **Staged electric resistance heating**
- **Variable capacity HVAC systems**

## How It Works

### Database-Driven Configuration

All HVAC stages are stored in the database (`hvac_stages` table) rather than being hardcoded. This provides:

- **Flexibility**: Add, remove, or modify stages without code changes
- **Per-Stage Configuration**: Each stage has its own GPIO pin, temperature offset, and minimum run time
- **Easy Management**: Configure via web interface or SQL queries
- **Backwards Compatibility**: Existing systems auto-migrate to new schema

### Progressive Stage Activation

Stages activate progressively based on how far the temperature is from target:

**Heating Example:**
- Temperature is 2°F below target → Stage 1 activates
- Temperature is 5°F below target → Stages 1 + 2 activate
- Temperature is 8°F below target → Stages 1 + 2 + 3 activate

**Cooling Example:**
- Temperature is 2°F above target → Stage 1 activates
- Temperature is 5°F above target → Stages 1 + 2 activate

### Safety Protections

- **Heat/Cool Interlock**: Never activates heating and cooling simultaneously
- **Per-Stage Minimum Run Time**: Each stage respects its configured minimum run time
- **Per-Stage Minimum Rest Time**: Stages won't rapid-cycle on/off
- **Gradual Activation**: Higher stages only activate when lower stages are insufficient

## Database Schema

### `hvac_stages` Table

```sql
CREATE TABLE hvac_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_type TEXT NOT NULL,           -- 'heat' or 'cool'
    stage_number INTEGER NOT NULL,      -- 1, 2, 3, etc.
    gpio_pin INTEGER NOT NULL,          -- BCM GPIO pin number
    temp_offset REAL NOT NULL,          -- Temperature offset in Celsius
    min_run_time INTEGER DEFAULT 300,   -- Minimum run time in seconds
    enabled INTEGER DEFAULT 1,          -- 1=enabled, 0=disabled
    description TEXT,                   -- Human-readable description
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(stage_type, stage_number)
);
```

### Default Configuration

On first run, the system creates these default stages:

| Type | Stage | GPIO | Temp Offset | Min Run Time | Description |
|------|-------|------|-------------|--------------|-------------|
| heat | 1 | 17 | 0.28°C (~0.5°F) | 300s | Primary heating |
| heat | 2 | 23 | 1.67°C (~3°F) | 300s | Secondary/auxiliary heating |
| cool | 1 | 27 | 0.28°C (~0.5°F) | 300s | Primary cooling |

## Configuration

### Adding a New Stage (SQL)

To add a third heating stage:

```sql
INSERT INTO hvac_stages 
    (stage_type, stage_number, gpio_pin, temp_offset, min_run_time, enabled, description)
VALUES 
    ('heat', 3, 24, 2.78, 300, 1, 'Emergency heat');
```

This stage will activate when temperature is ~5°F below target.

### Adding a Second Cooling Stage (SQL)

```sql
INSERT INTO hvac_stages 
    (stage_type, stage_number, gpio_pin, temp_offset, min_run_time, enabled, description)
VALUES 
    ('cool', 2, 16, 1.67, 300, 1, 'High-speed cooling');
```

### Modifying Stage Settings (SQL)

To change the temperature offset for stage 2 heating:

```sql
UPDATE hvac_stages 
SET temp_offset = 1.11 
WHERE stage_type = 'heat' AND stage_number = 2;
```

### Disabling a Stage (SQL)

To temporarily disable a stage without deleting it:

```sql
UPDATE hvac_stages 
SET enabled = 0 
WHERE stage_type = 'heat' AND stage_number = 3;
```

### Deleting a Stage (SQL)

```sql
DELETE FROM hvac_stages 
WHERE stage_type = 'heat' AND stage_number = 3;
```

## Temperature Offset Guidelines

The `temp_offset` determines when a stage activates. It's the **temperature deficit/excess** required, stored in **Celsius**.

### Heating Stage Offsets (typical)

| Offset (°C) | Offset (°F) | When to Use |
|-------------|-------------|-------------|
| 0.28 | 0.5 | Stage 1 (always activates first) |
| 1.67 | 3.0 | Stage 2 (auxiliary/secondary heat) |
| 2.78 | 5.0 | Stage 3 (emergency heat) |
| 4.44 | 8.0 | Stage 4 (extreme cold backup) |

### Cooling Stage Offsets (typical)

| Offset (°C) | Offset (°F) | When to Use |
|-------------|-------------|-------------|
| 0.28 | 0.5 | Stage 1 (always activates first) |
| 1.67 | 3.0 | Stage 2 (high-speed cooling) |
| 2.78 | 5.0 | Stage 3 (maximum capacity) |

### Calculating Offsets

To convert Fahrenheit to Celsius for database entry:

```
temp_offset_celsius = (temp_offset_fahrenheit * 5) / 9
```

Examples:
- 0.5°F = 0.28°C
- 3.0°F = 1.67°C
- 5.0°F = 2.78°C

## Minimum Run Time

Each stage can have its own `min_run_time` (in seconds). This prevents:

- **Short-cycling**: Equipment turning on/off too frequently
- **Compressor damage**: Compressors need minimum run time
- **Efficiency loss**: HVAC systems are most efficient with longer run cycles

**Typical values:**
- **300 seconds (5 min)**: Standard for most equipment
- **600 seconds (10 min)**: Heat pumps in cold weather
- **180 seconds (3 min)**: Electric resistance heat (faster response)

## Example Configurations

### Dual-Fuel System (Heat Pump + Gas Furnace)

```sql
-- Heat pump stage 1 (primary)
INSERT INTO hvac_stages VALUES 
    (1, 'heat', 1, 17, 0.28, 300, 1, 'Heat pump stage 1');

-- Heat pump stage 2 (high capacity)
INSERT INTO hvac_stages VALUES 
    (2, 'heat', 2, 23, 1.67, 300, 1, 'Heat pump stage 2');

-- Gas furnace (emergency/backup)
INSERT INTO hvac_stages VALUES 
    (3, 'heat', 3, 24, 3.33, 600, 1, 'Gas furnace backup');

-- Single stage cooling
INSERT INTO hvac_stages VALUES 
    (4, 'cool', 1, 27, 0.28, 300, 1, 'Cooling');
```

### Three-Stage Electric Heat

```sql
-- Stage 1: 5kW
INSERT INTO hvac_stages VALUES 
    (1, 'heat', 1, 17, 0.28, 180, 1, '5kW electric heat');

-- Stage 2: 10kW (adds 5kW more)
INSERT INTO hvac_stages VALUES 
    (2, 'heat', 2, 23, 1.67, 180, 1, '10kW electric heat');

-- Stage 3: 15kW (adds 5kW more)
INSERT INTO hvac_stages VALUES 
    (3, 'heat', 3, 24, 2.78, 180, 1, '15kW electric heat');
```

### Two-Stage Cooling

```sql
-- Stage 1: Low speed (60% capacity)
INSERT INTO hvac_stages VALUES 
    (1, 'cool', 1, 27, 0.28, 300, 1, 'Cooling stage 1 (low)');

-- Stage 2: High speed (100% capacity)
INSERT INTO hvac_stages VALUES 
    (2, 'cool', 2, 16, 1.67, 300, 1, 'Cooling stage 2 (high)');
```

## Wiring Diagram

### Typical Multi-Stage Heat Pump

```
Thermostat     Relay Board    HVAC System
-----------    -----------    -----------
GPIO 17   -->  Relay 1 NO --> W1 (Heat Stage 1)
GPIO 23   -->  Relay 2 NO --> W2 (Heat Stage 2)
GPIO 27   -->  Relay 3 NO --> Y1 (Cool Compressor)
GPIO 22   -->  Relay 4 NO --> G  (Fan)
```

### Four-Relay Board (2 Heat + 1 Cool + Fan)

```
GPIO Pin    Relay    HVAC Terminal    Function
--------    -----    -------------    --------
   17         1      W1 (or W)        Primary Heat
   23         2      W2 (or E)        Secondary/Emergency Heat
   27         3      Y (or Y1)        Cooling Compressor
   22         4      G                Fan
```

## Monitoring Active Stages

### Web Interface

The dashboard shows active stages:
- "HVAC: HEAT[1] + FAN" - Only stage 1 heating
- "HVAC: HEAT[1, 2] + FAN" - Both heating stages active
- "HVAC: COOL[1, 2] + FAN" - Two-stage cooling active

### Log Files

```
INFO - HVAC state: HEAT[1] + FAN
INFO - Heat Stage 2 ON: GPIO 23
INFO - HVAC state: HEAT[1, 2] + FAN
```

### Database Queries

Recent HVAC activity with stage information:

```sql
SELECT 
    datetime(timestamp, 'localtime') as time,
    system_temp,
    hvac_mode,
    active_stages,
    heat_active,
    cool_active
FROM hvac_history 
WHERE timestamp > datetime('now', '-1 day')
ORDER BY timestamp DESC 
LIMIT 20;
```

## Troubleshooting

### Stage Not Activating

1. **Check if stage is enabled:**
   ```sql
   SELECT * FROM hvac_stages WHERE enabled = 1;
   ```

2. **Check temperature offset:**
   - Is the temperature deficit large enough to trigger the stage?
   - Stage 2 with offset 1.67°C needs temp 3°F below target

3. **Check minimum run time:**
   - Look for log message: "stage X minimum rest time not met"
   - Wait for min_run_time to expire

4. **Check GPIO wiring:**
   - Verify correct GPIO pin in database
   - Test relay manually with `gpio test_relays.py`

### Stage Activating Too Early/Late

Adjust the `temp_offset`:

```sql
-- Make stage activate sooner (reduce offset)
UPDATE hvac_stages 
SET temp_offset = 0.83  -- Was 1.67 (~3°F, now ~1.5°F)
WHERE stage_type = 'heat' AND stage_number = 2;

-- Make stage activate later (increase offset)
UPDATE hvac_stages 
SET temp_offset = 2.78  -- Was 1.67 (~3°F, now ~5°F)
WHERE stage_type = 'heat' AND stage_number = 2;
```

### Stage Short-Cycling

Increase `min_run_time`:

```sql
UPDATE hvac_stages 
SET min_run_time = 600  -- Increase from 300s to 600s (10 minutes)
WHERE stage_type = 'heat' AND stage_number = 2;
```

## Migration from Old System

### Automatic Migration

On first run with the new code, the database automatically:

1. Creates the `hvac_stages` table
2. Adds `active_stages` column to `hvac_history`
3. Populates default stages using GPIO pins from `config.env`

### Manual Migration (if needed)

If you need to recreate default stages:

```sql
-- Delete existing stages
DELETE FROM hvac_stages;

-- Recreate defaults
INSERT INTO hvac_stages (stage_type, stage_number, gpio_pin, temp_offset, min_run_time, enabled, description)
VALUES 
    ('heat', 1, 17, 0.28, 300, 1, 'Primary heating'),
    ('heat', 2, 23, 1.67, 300, 1, 'Secondary/auxiliary heating'),
    ('cool', 1, 27, 0.28, 300, 1, 'Primary cooling');
```

## Performance Considerations

### Database Queries

- Stage configurations are loaded once at startup
- No database queries during normal HVAC control loop
- Very low overhead

### GPIO Operations

- Only changed relays are toggled (not all relays every cycle)
- Minimum timing enforced per-stage, not globally
- Efficient state tracking

## Future Enhancements

Potential additions for future versions:

- [ ] Web UI for stage configuration (currently SQL only)
- [ ] Stage activation history graphs
- [ ] Advanced staging algorithms (outdoor temp-based)
- [ ] Stage energy usage tracking
- [ ] Lockout temperatures per stage
- [ ] Time-of-day stage restrictions
- [ ] Stage priority/preference settings

## API Reference

### Database Methods

```python
# Get all enabled stages for a type
db.get_hvac_stages(stage_type='heat', enabled_only=True)

# Add a new stage
db.add_hvac_stage(
    stage_type='heat',
    stage_number=3,
    gpio_pin=24,
    temp_offset=2.78,  # ~5°F
    min_run_time=300,
    enabled=True,
    description='Emergency heat'
)

# Update a stage
db.update_hvac_stage(
    stage_id=2,
    temp_offset=1.11,  # Change activation point
    min_run_time=600   # Change minimum run time
)

# Delete a stage
db.delete_hvac_stage(stage_id=3)
```

### Controller Properties

```python
# Access active stages in thermostat code
controller.active_heat_stages  # [1, 2] means stages 1 and 2 are on
controller.active_cool_stages  # [1] means stage 1 cooling is on

# Access stage configurations
controller.heating_stages  # List of heat stage dicts
controller.cooling_stages  # List of cool stage dicts
```

## Support

For questions or issues with multi-stage HVAC:

1. Check logs: `tail -f /var/log/thermostat.log`
2. Review stage configuration: `sqlite3 thermostat.db "SELECT * FROM hvac_stages"`
3. Test relays individually: `python tests/test_relays.py`
4. Review control logic: See `src/thermostat.py` → `control_hvac()`

## References

- **HVAC Staging Best Practices**: See CONTROL_ARCHITECTURE.md
- **Database Schema**: See database.py → `_init_database()`
- **GPIO Wiring**: See PARTS_LIST.md
- **Safety Features**: See CONTROL_FEATURES.md
