# Web Interface Settings Feature

## Overview

Added a comprehensive Settings page to the web interface allowing users to:
- Change temperature display units (Fahrenheit, Celsius, or Kelvin)
- Rename sensors with friendly names (e.g., "Living Room", "Bedroom")
- Enable/disable individual sensors
- View system and database information

All enabled sensors are automatically monitored for anomalies (like rapid temperature changes from a fireplace).

## Files Changed

### New Files
- `src/templates/settings.html` - Settings page UI with sensor configuration interface

### Modified Files
- `src/web_interface.py` - Added `/settings` route
- `src/templates/dashboard.html` - Added Settings link to navigation
- `src/templates/schedules.html` - Added Settings link to navigation
- `src/templates/history.html` - Added Settings link to navigation
- `src/static/css/common.css` - Added CSS variables for settings page styling
- `README.md` - Documented the new Settings page
- `tests/unit/test_web_interface_unit.py` - Added tests for Settings page

## Features

### Temperature Unit Conversion
Users can switch between:
- **Fahrenheit (°F)** - Default
- **Celsius (°C)**
- **Kelvin (K)**

Changes apply immediately across all pages and are persisted to the database.

### Sensor Configuration
For each sensor, users can:
1. **Set Display Name** - Replace sensor IDs with meaningful names
2. **Enable/Disable** - Control which sensors are included in temperature calculations

**Note:** All enabled sensors are automatically monitored for anomalies such as rapid temperature changes (e.g., fireplace turning on). The system will temporarily exclude sensors from HVAC control when anomalies are detected.

### System Information
View real-time statistics:
- Database file path and size
- Number of logged sensor readings
- Number of logged HVAC events

## API Endpoints

### GET `/settings`
Renders the settings page

### GET `/api/sensors/config`
Returns all sensor configurations
```json
{
  "sensors": [
    {
      "sensor_id": "28-000000001234",
      "name": "Living Room",
      "enabled": true,
      "monitored": true
    }
  ]
}
```

### PUT `/api/sensors/config/{sensor_id}`
Update sensor configuration. The `monitored` field is automatically set to match the `enabled` state.
```json
{
  "name": "Living Room",
  "enabled": true
}
```

### DELETE `/api/sensors/config/{sensor_id}`
Delete sensor configuration (removes from database, not from hardware)

### GET `/api/database/stats`
Returns database statistics
```json
{
  "database_path": "thermostat.db",
  "database_size_bytes": 1048576,
  "sensor_history_count": 5000,
  "hvac_history_count": 1000
}
```

## User Interface

The Settings page follows the same design pattern as other pages:
- Responsive layout that works on mobile devices
- Dark/light theme support
- Clean, intuitive interface with clear labels
- Real-time feedback on changes
- Input validation with helpful error messages

### Navigation
All pages now include a "Settings" link in the navigation bar:
- Dashboard → Schedules → History → **Settings**

## Testing

All new functionality is covered by unit tests:
- `TestSettingsPage` - 9 tests covering all settings endpoints
- Tests verify proper error handling and database interactions
- All tests passing ✓

## Safety Considerations

- Disabling all sensors will not crash the system (graceful degradation)
- Temperature unit changes are validated (F, C, K only)
- Sensor configuration changes don't affect running HVAC operations
- Database errors are handled gracefully with user-friendly messages

## Future Enhancements

Potential additions to Settings page:
- HVAC timing configuration (min run/rest times)
- Anomaly detection threshold tuning
- History retention settings
- System logs viewer
- Network configuration
- Backup/restore database

## Usage Example

1. Navigate to `http://your-raspberry-pi-ip:5000/settings`
2. Change temperature units by selecting F, C, or K
3. Click on a sensor's name field to rename it
4. Check/uncheck "Enabled" to include/exclude sensor from HVAC control
5. Click "Save Changes" for each sensor modified

All changes are immediately saved to the database and take effect on the next sensor read cycle. Enabled sensors are automatically monitored for anomalies.
