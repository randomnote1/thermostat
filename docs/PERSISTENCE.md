# Persistence, Scheduling & History Features

## Overview

Your thermostat now includes comprehensive persistence capabilities with scheduling and history tracking. All data is stored in a local SQLite database that survives reboots and provides valuable insights into system operation.

## New Features

### 1. **Temperature Setting Persistence** ✅
- All temperature changes are automatically saved
- Settings survive restarts and power loss
- No more manual config file editing

### 2. **Schedule Management** 📅
- Create time-based temperature programs
- Different schedules for weekdays/weekends
- Automatic mode switching
- Web-based schedule editor

### 3. **History Logging** 📊
- Sensor readings logged every 5 minutes
- HVAC activity tracked
- Setting changes audit trail
- Web-based history viewer

## Database Schema

### Tables

**settings** - Current thermostat configuration
- target_temp_heat, target_temp_cool
- hvac_mode, fan_mode
- Persists across restarts

**schedules** - Time-based temperature programs
- name, days_of_week, time
- target temperatures and mode
- enabled/disabled flag

**setting_history** - Audit log of all changes
- What changed, old/new values
- When it changed, who changed it

**sensor_history** - Temperature readings over time
- sensor_id, temperature, timestamp
- compromised flag
- Used for graphs and analysis

**hvac_history** - HVAC activity log
- System temp, target temp, mode
- Heat/cool/fan states
- Used for runtime tracking

## Quick Start

### 1. Database Configuration

Add to `config.env`:
```bash
# Database & History
DATABASE_PATH=thermostat.db
HISTORY_LOG_INTERVAL=300  # Seconds (5 minutes default)
```

### 2. Start Thermostat

```bash
python src/thermostat.py
```

The database is automatically created on first run.

### 3. Access Web Interface

```
http://<raspberry-pi-ip>:5000
```

Navigate between pages:
- **Dashboard** - Real-time monitoring and control
- **Schedules** - Create and manage schedules
- **History** - View logs and statistics

## Creating Schedules

### Via Web Interface

1. Go to **http://\<pi-ip\>:5000/schedules**
2. Click "Create New Schedule"
3. Fill in the form:
   - **Name**: e.g., "Weekday Morning"
   - **Days**: Select Mon-Fri
   - **Time**: e.g., 06:00
   - **Heat Temp**: e.g., 70°F
   - **Cool Temp**: Optional
   - **Mode**: Optional (heat/cool/auto/off)
4. Click "Save Schedule"

### Via API

```bash
curl -X POST http://192.168.1.100:5000/api/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekday Morning",
    "days_of_week": "Mon,Tue,Wed,Thu,Fri",
    "time": "06:00",
    "target_temp_heat": 70.0,
    "target_temp_cool": null,
    "hvac_mode": "heat"
  }'
```

### Schedule Examples

**Weekday Sleep Schedule**
```
Name: Weekday Sleep
Days: Mon, Tue, Wed, Thu, Fri
Time: 22:00
Heat: 65°F
Cool: 78°F
Mode: auto
```

**Weekend Morning**
```
Name: Weekend Morning
Days: Sat, Sun
Time: 08:00
Heat: 72°F
Cool: 74°F
Mode: auto
```

**Away Mode (All Days)**
```
Name: Work Hours
Days: Mon, Tue, Wed, Thu, Fri
Time: 08:00
Heat: 62°F
Cool: 80°F
Mode: auto
```

## Viewing History

### Web Interface

Go to **http://\<pi-ip\>:5000/history** to view:

**Database Statistics**
- Total sensor readings
- HVAC runtime logs
- Setting changes
- Database size

**Setting Changes**
- What changed (temperature, mode, etc.)
- Old and new values
- When and how (web, schedule, manual)

**HVAC Activity**
- System temperature over time
- What was running (heat/cool/fan)
- Mode and target temperature

**Sensor Readings**
- All sensor temperatures
- Compromised sensor flags
- Historical trends

### API Access

**Get Sensor History**
```bash
# Last 24 hours of all sensors
curl http://192.168.1.100:5000/api/history/sensors?hours=24

# Specific sensor
curl http://192.168.1.100:5000/api/history/sensors?sensor_id=28-0000000001

# Last 7 days
curl http://192.168.1.100:5000/api/history/sensors?hours=168
```

**Get HVAC History**
```bash
curl http://192.168.1.100:5000/api/history/hvac?hours=24
```

**Get Setting Changes**
```bash
curl http://192.168.1.100:5000/api/history/settings?limit=100
```

## How It Works

### Persistence Flow

```
User changes temperature via web interface
    │
    ▼
Thermostat.handle_control_command()
    │
    ├── Update in-memory variable
    ├── Save to database (settings table)
    └── Log change (setting_history table)
    │
    ▼
[System Restart]
    │
    ▼
Thermostat.__init__()
    │
    ├── Load from config.env (defaults)
    └── Override with database values (persisted)
    │
    ▼
Settings restored! 🎉
```

### Schedule Execution

```
Main Control Loop (every 60 seconds)
    │
    ▼
Check current time: 06:00 on Monday
    │
    ▼
Query database for active schedules
    │
    ▼
Found: "Weekday Morning" schedule
    ├── target_temp_heat: 70°F
    ├── target_temp_cool: 74°F
    └── hvac_mode: heat
    │
    ▼
Apply settings
    ├── Update thermostat variables
    ├── Save to database
    └── Log change (source: "schedule:Weekday Morning")
    │
    ▼
HVAC adjusts to new settings
```

### History Logging

```
Main Control Loop
    │
    ├── Read sensors (every 30s)
    ├── Control HVAC (every 60s)
    │
    ▼
Every 5 minutes (HISTORY_LOG_INTERVAL)
    │
    ├── Log all sensor readings
    │   └── INSERT INTO sensor_history
    │
    └── Log HVAC state
        └── INSERT INTO hvac_history
```

## Database Management

### Viewing Database

```bash
# Connect to database
sqlite3 thermostat.db

# View tables
.tables

# View schedules
SELECT * FROM schedules;

# View recent setting changes
SELECT * FROM setting_history ORDER BY timestamp DESC LIMIT 10;

# View sensor readings for last hour
SELECT * FROM sensor_history 
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;
```

### Cleanup Old Data

The database includes a cleanup function:

```python
from src.database import ThermostatDatabase

db = ThermostatDatabase()
db.cleanup_old_history(days_to_keep=30)  # Keep last 30 days
```

**Automated Cleanup** (add to cron):
```bash
# Run cleanup monthly
0 0 1 * * python3 /path/to/cleanup_script.py
```

### Backup Database

```bash
# Simple file copy (stop thermostat first)
sudo systemctl stop thermostat
cp thermostat.db thermostat_backup_$(date +%Y%m%d).db
sudo systemctl start thermostat

# Or use SQLite backup command
sqlite3 thermostat.db ".backup thermostat_backup.db"
```

### Reset Database

```bash
# Stop thermostat
sudo systemctl stop thermostat

# Remove database
rm thermostat.db

# Restart (creates fresh database)
sudo systemctl start thermostat
```

## API Reference

### Schedule Endpoints

**GET /api/schedules**
- List all schedules

**POST /api/schedules**
- Create new schedule
- Body: `{name, days_of_week, time, target_temp_heat?, target_temp_cool?, hvac_mode?}`

**PUT /api/schedules/<id>**
- Update schedule
- Body: Any schedule fields

**DELETE /api/schedules/<id>**
- Delete schedule

### History Endpoints

**GET /api/history/sensors**
- Query params: `sensor_id?, hours=24, limit=1000`

**GET /api/history/hvac**
- Query params: `hours=24, limit=1000`

**GET /api/history/settings**
- Query params: `limit=100`

**GET /api/database/stats**
- Database statistics

## Performance Considerations

### Database Size Growth

Typical growth rates:
- **Sensor readings**: ~1KB per reading
  - 6 sensors × 12 readings/hour = 72 readings/hour
  - 72 × 24 × 30 = 51,840 readings/month (~50MB/month)

- **HVAC history**: ~200 bytes per record
  - 12 records/hour × 24 × 30 = 8,640 records/month (~2MB/month)

- **Setting history**: Minimal (~1KB per change)

**Total**: ~50-60MB per month with default settings

### Optimization Tips

1. **Increase logging interval** for less data:
   ```bash
   HISTORY_LOG_INTERVAL=600  # 10 minutes instead of 5
   ```

2. **Regular cleanup**:
   ```bash
   # Keep only 30 days
   db.cleanup_old_history(days_to_keep=30)
   ```

3. **Database vacuuming** (monthly):
   ```bash
   sqlite3 thermostat.db "VACUUM;"
   ```

## Troubleshooting

### Database Locked Error

**Symptom**: "database is locked" errors in logs

**Solution**:
```bash
# Ensure only one thermostat instance running
ps aux | grep thermostat

# Or restart service
sudo systemctl restart thermostat
```

### Schedules Not Applying

**Check schedule configuration**:
```sql
sqlite3 thermostat.db
SELECT * FROM schedules WHERE enabled = 1;
```

**Verify day format**: Use "Mon,Tue,Wed" or "0,1,2" (0=Monday)

**Check time format**: Use "HH:MM" (e.g., "06:00", "18:30")

**View logs**:
```bash
sudo journalctl -u thermostat.service | grep schedule
```

### History Not Logging

**Check HISTORY_LOG_INTERVAL**:
```bash
grep HISTORY_LOG_INTERVAL config.env
```

**Verify database exists**:
```bash
ls -lh thermostat.db
```

**Check logs for errors**:
```bash
sudo journalctl -u thermostat.service | grep history
```

### Web Interface Shows "Database not available"

**Verify database initialized**:
```bash
python3 -c "from src.database import ThermostatDatabase; db = ThermostatDatabase(); print('OK')"
```

**Check web interface database reference**:
- Ensure `set_database(self.db)` is called in thermostat.py

## Migration from Old System

If you have an existing thermostat without persistence:

### 1. Update Code
```bash
git pull  # Or update manually
```

### 2. Check Config
```bash
# Add to config.env
DATABASE_PATH=thermostat.db
HISTORY_LOG_INTERVAL=300
```

### 3. First Run
```bash
python3 src/thermostat.py
```

Current settings from config.env will be used initially, then saved to database.

### 4. Verify
```bash
# Check database created
ls -lh thermostat.db

# View persisted settings
sqlite3 thermostat.db "SELECT * FROM settings;"
```

## Future Enhancements

Potential features for development:
- [ ] Temperature graphs (Chart.js integration)
- [ ] Export history to CSV
- [ ] Schedule templates (vacation mode, etc.)
- [ ] Recurring schedule exceptions
- [ ] Geofencing (home/away detection)
- [ ] Energy usage estimates
- [ ] Predictive maintenance alerts
- [ ] Multi-user access control

## Related Documentation

- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Web dashboard guide
- [CONTROL_FEATURES.md](CONTROL_FEATURES.md) - Remote control guide
- [TESTING.md](TESTING.md) - Testing procedures
- [README.md](../README.md) - Project overview

## Support

**Issues?**
1. Check logs: `sudo journalctl -u thermostat.service -f`
2. Verify database: `sqlite3 thermostat.db ".tables"`
3. Test database module: `python3 -c "from src.database import ThermostatDatabase; db = ThermostatDatabase('test.db')"`
4. Check web interface: `curl http://localhost:5000/api/database/stats`

**Questions?**
- Review database schema in [src/database.py](../src/database.py)
- Check API endpoints in [src/web_interface.py](../src/web_interface.py)
