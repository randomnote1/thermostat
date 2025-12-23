# Schedule Override System

## Overview

The schedule override system provides flexible control over automated schedules, allowing you to make manual adjustments without being immediately overridden by the next scheduled event.

## How It Works

### Manual Hold (Default Behavior)

When you manually change any setting (temperature, mode) through the web interface, the system automatically places schedules "on hold" for a configurable period (default: **2 hours**).

**Example Scenario:**
- Schedule set for 68°F at 6:00 AM
- You manually adjust to 72°F at 7:30 AM
- Schedules are placed on hold until 9:30 AM
- Next schedule at 8:00 PM will still run as normal

### Three Operating States

1. **Active** (✅)
   - Schedules are running normally
   - Next scheduled event will execute at its designated time
   
2. **On Hold** (⏸️)
   - Manual change detected
   - Schedules paused for configured duration
   - Shows countdown timer in web interface
   
3. **Disabled** (🔕)
   - All schedules globally disabled
   - No automatic changes will occur
   - Must be manually re-enabled

## Configuration

### config.env Settings

```bash
# Enable or disable schedule execution
SCHEDULE_ENABLED=true

# Hours to hold manual changes before resuming schedules
# Set to 0 to disable hold feature (schedules always run)
SCHEDULE_HOLD_HOURS=2
```

### Hold Duration Examples

| Setting | Behavior |
|---------|----------|
| `SCHEDULE_HOLD_HOURS=0` | No hold - next schedule overrides immediately |
| `SCHEDULE_HOLD_HOURS=1` | 1 hour hold after manual change |
| `SCHEDULE_HOLD_HOURS=2` | 2 hours hold (default, good for short adjustments) |
| `SCHEDULE_HOLD_HOURS=4` | 4 hours hold (good for morning/afternoon overrides) |
| `SCHEDULE_HOLD_HOURS=24` | Full day hold (manual control until next day's schedule) |

## Web Interface Controls

### Schedule Status Display

Located in the **System Controls** card on the dashboard:

- **Green banner**: Schedules active and running
- **Red banner**: Schedules on hold with countdown timer
- **Orange banner**: Schedules globally disabled

### Control Buttons

**Resume Schedules**
- Clears manual hold immediately
- Next scheduled event will execute at its time
- Only visible when schedules are on hold

**Disable Schedules**
- Globally disables all schedule execution
- Requires confirmation
- Manual control only until re-enabled

**Enable Schedules**
- Re-enables globally disabled schedules
- Only visible when schedules are disabled

## Use Cases

### Temporary Override
*"I want to make the house warmer for a few hours without affecting tonight's schedule"*

1. Adjust temperature via web interface
2. Schedules automatically go on hold for 2 hours
3. After 2 hours, automatic scheduling resumes
4. Evening schedule at 8:00 PM will still execute

### Extended Manual Control
*"I'm working from home today and want manual control"*

1. Set `SCHEDULE_HOLD_HOURS=8` (or more)
2. Make manual adjustment
3. Schedules won't resume for 8 hours
4. Or click "Resume Schedules" when ready for automation

### Disable Automation Temporarily
*"We're having a party and need full manual control"*

1. Click "Disable Schedules" button
2. Make temperature adjustments as needed
3. Schedules won't execute at all
4. Click "Enable Schedules" when ready to resume automation

### Vacation Mode
*"We're away for the week, keep one temperature setting"*

**Option 1**: Disable schedules and set a fixed temperature
1. Click "Disable Schedules"
2. Set desired temperature (e.g., 60°F in winter)
3. System maintains that temperature until you return

**Option 2**: Create a vacation schedule
1. Create a schedule named "Vacation" 
2. Set for all days, multiple times per day
3. Disable other schedules temporarily

## Logging and History

All schedule-related events are logged:

**Setting History Log:**
```
2024-01-15 07:30:00 | target_temp_heat | 68 → 72 | web_interface
2024-01-15 07:30:01 | schedule_hold | enabled → until 09:30:00
2024-01-15 09:30:00 | schedule_hold | expired
2024-01-15 20:00:00 | target_temp_heat | 72 → 68 | schedule:Evening
```

**View in Web Interface:**
- Navigate to **History** page
- Select **Setting Changes** tab
- Filter by source: "web_interface" or "schedule:*"

## API Endpoints

### Check Schedule Status
```bash
GET /api/status
```

Response includes:
```json
{
  "schedule_enabled": true,
  "schedule_on_hold": true,
  "schedule_hold_until": "2024-01-15T09:30:00",
  ...
}
```

### Resume Schedules
```bash
POST /api/schedules/control
Content-Type: application/json

{
  "action": "resume"
}
```

### Enable/Disable Schedules
```bash
POST /api/schedules/control
Content-Type: application/json

{
  "action": "enable"  // or "disable"
}
```

## Best Practices

### For Most Users (Recommended)
```bash
SCHEDULE_ENABLED=true
SCHEDULE_HOLD_HOURS=2
```
- Allows quick manual adjustments
- Schedules resume automatically after 2 hours
- Good balance between flexibility and automation

### For Frequent Manual Control
```bash
SCHEDULE_ENABLED=true
SCHEDULE_HOLD_HOURS=4
```
- Longer hold duration
- Better for users who frequently override schedules
- Schedules still run eventually

### For Full Automation
```bash
SCHEDULE_ENABLED=true
SCHEDULE_HOLD_HOURS=0
```
- No hold period
- Next schedule always executes at its time
- Manual changes only last until next scheduled event
- Best for users who rarely need manual control

### For Manual-Only Operation
```bash
SCHEDULE_ENABLED=false
```
- Completely disables schedule automation
- Full manual control
- Can be toggled via web interface

## Troubleshooting

### Schedule Didn't Execute

**Check schedule status:**
1. Open dashboard
2. Look for schedule status banner
3. If "On Hold", click "Resume Schedules"

**Verify schedule is enabled:**
```bash
# In database or schedules page
SELECT * FROM schedules WHERE enabled = 1;
```

### Can't Resume Schedules

**Check configuration:**
- Verify `SCHEDULE_ENABLED=true` in config.env
- Restart service if config was changed

**Check web interface:**
- Ensure no JavaScript errors in browser console
- Verify API endpoint responds: `/api/schedules/control`

### Hold Duration Too Short/Long

**Adjust in config.env:**
```bash
# Change to desired number of hours
SCHEDULE_HOLD_HOURS=4

# Restart service
sudo systemctl restart thermostat
```

## Technical Details

### Hold Implementation

When a manual change occurs:
1. `handle_control_command()` calls `_set_schedule_hold()`
2. `schedule_hold_until` timestamp is set to `now + SCHEDULE_HOLD_HOURS`
3. `_check_schedules()` skips execution while hold is active
4. Hold automatically expires when `now >= schedule_hold_until`

### Schedule Check Logic

```python
def _check_schedules(current_time):
    # 1. Check if globally disabled
    if not self.schedule_enabled:
        return
    
    # 2. Check if manual hold is active
    if self.schedule_hold_until and current_time < self.schedule_hold_until:
        return  # Skip schedule execution
    
    # 3. Clear expired hold
    if self.schedule_hold_until and current_time >= self.schedule_hold_until:
        self.schedule_hold_until = None
    
    # 4. Execute active schedules
    for schedule in get_active_schedules(current_time):
        apply_schedule(schedule)
```

### Database Schema

No database changes required - hold state is maintained in memory only. This means:
- Hold state resets on service restart
- No persistence overhead
- Clean slate after reboot

If you need persistent holds across restarts, you could add:
```sql
ALTER TABLE settings ADD COLUMN schedule_hold_until TEXT;
```

## See Also

- [PERSISTENCE.md](PERSISTENCE.md) - Full database and history documentation
- [schedules.html](../src/templates/schedules.html) - Schedule management interface
- [dashboard.html](../src/templates/dashboard.html) - Main control interface
