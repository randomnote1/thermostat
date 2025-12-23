# Web Interface Control Features

## Overview

The thermostat web interface now supports **full remote control** in addition to monitoring. You can adjust temperatures, switch modes, and control the fan from any device on your local network.

## What's New

✅ **Temperature Controls**
- +/− buttons for heating and cooling setpoints
- Adjust in 1°F increments
- Range: 50°F to 90°F
- Instant feedback with success messages

✅ **HVAC Mode Control**
- OFF - System completely off
- HEAT - Heating mode only
- COOL - Cooling mode only
- AUTO - Automatic switching (future implementation)

✅ **Manual Fan Control**
- Toggle switch for independent fan operation
- ON - Fan runs continuously
- OFF - Fan runs only when heating/cooling active

✅ **Safety Features**
- Temperature limits enforced (50-90°F)
- Invalid inputs rejected
- Heat and cool never run simultaneously
- All changes logged to system log

## Quick Start

### 1. Ensure Flask is Installed

```bash
pip install Flask==3.0.0
```

### 2. Enable Web Interface

In `config.env`:
```bash
WEB_INTERFACE_ENABLED=true
WEB_PORT=5000
```

### 3. Start Thermostat

```bash
python3 src/thermostat.py
```

### 4. Access Dashboard

```
http://<raspberry-pi-ip>:5000
```

## Using the Controls

### Adjusting Temperature Setpoints

1. Locate the "Target Temperatures" card
2. Click **+** to increase or **−** to decrease
3. Each click adjusts by 1°F
4. Green success message confirms change
5. Dashboard updates automatically within 5 seconds

**Example:**
- Current heating setpoint: 68°F
- Click **+** button twice → 70°F
- Message: "Target heat temperature set to 70°F"

### Changing HVAC Mode

1. Locate the "System Controls" card
2. Click the desired mode button:
   - **OFF** - Turns everything off
   - **HEAT** - Activates heating mode
   - **COOL** - Activates cooling mode
   - **AUTO** - Switches automatically between heat/cool

3. Active mode button is highlighted
4. Success message confirms mode change

### Controlling the Fan

1. Locate the "Fan Control" toggle in the "System Controls" card
2. Click the toggle switch:
   - **ON** (green) - Fan runs continuously
   - **OFF** (gray) - Fan runs only when heating/cooling

3. Label updates to show current state
4. Success message confirms change

## Safety & Validation

### Built-in Protections

**Temperature Limits:**
- Minimum: 50°F (prevents freezing)
- Maximum: 90°F (prevents overheating)
- Attempts outside range show error message

**HVAC Interlocks:**
- Heat and cool never run simultaneously
- Setting mode to "OFF" immediately shuts down all HVAC
- Minimum run/rest times still enforced (5 minutes default)

**Input Validation:**
- All control commands validated before execution
- Invalid inputs rejected with clear error messages
- Malformed requests logged for troubleshooting

### Logging

All control changes are logged to system log:

```
INFO - Control command received: set_temperature with params {'type': 'heat', 'temperature': 70.0}
INFO - Target heat temperature set to 70.0°F
INFO - Control command received: set_mode with params {'mode': 'cool'}
INFO - HVAC mode set to cool
```

View logs:
```bash
sudo journalctl -u thermostat.service -f
```

## API Access

Control the thermostat programmatically using the REST API.

### Set Temperature

```bash
curl -X POST http://192.168.1.100:5000/api/control/temperature \
  -H "Content-Type: application/json" \
  -d '{"type":"heat","temperature":72}'
```

### Set Mode

```bash
curl -X POST http://192.168.1.100:5000/api/control/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"cool"}'
```

### Control Fan

```bash
curl -X POST http://192.168.1.100:5000/api/control/fan \
  -H "Content-Type: application/json" \
  -d '{"fan_on":true}'
```

### Response Format

**Success:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "message": "Target heat temperature set to 72°F"
  }
}
```

**Error:**
```json
{
  "error": "Temperature out of range (50-90°F)"
}
```

## Troubleshooting

### Controls Not Responding

**Check Flask is Running:**
```bash
# Look for "Web interface started on port 5000" in logs
sudo journalctl -u thermostat.service | grep "Web interface"
```

**Check Browser Console:**
- Press F12 in browser
- Look for network errors or JavaScript errors
- Verify API requests are being sent

**Clear Browser Cache:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux)
- Or: Cmd+Shift+R (Mac)

### Temperature Won't Change

**Verify Range:**
- Must be 50-90°F
- Check error message if rejected

**Check Current Value:**
- May already be at desired temperature
- Look at current setpoint in dashboard

**Review Logs:**
```bash
sudo journalctl -u thermostat.service -n 50
```

### Mode Changes Don't Take Effect

**Wait for Next Control Cycle:**
- Control loop runs every 60 seconds
- Mode change takes effect on next iteration

**Check Minimum Run/Rest Times:**
- HVAC won't change if minimum time not elapsed
- Default: 5 minutes run, 5 minutes rest

**Verify in Dashboard:**
- HVAC Status card shows actual equipment state
- May lag behind mode change

## Security Considerations

⚠️ **Important:** Control access grants full HVAC system control.

### Recommendations

1. **Network Security:**
   - Keep web interface on trusted home network only
   - Do not expose to internet without authentication
   - Use strong WiFi password (WPA3)

2. **Access Control:**
   - Consider firewall rules to limit access:
     ```bash
     sudo ufw allow from 192.168.1.0/24 to any port 5000
     ```
   - Monitor logs for unauthorized access attempts

3. **Physical Security:**
   - Secure Raspberry Pi physical location
   - Prevent unauthorized USB/keyboard access

4. **Monitoring:**
   - Review logs regularly
   - Look for unexpected temperature or mode changes

### Future Authentication

Planned enhancements:
- HTTP Basic Authentication
- User accounts with permissions
- API keys for automation
- Rate limiting
- HTTPS/TLS encryption

## Testing

Control functionality is fully tested with 17 unit tests:

```bash
pytest tests/unit/test_web_controls_unit.py -v
```

**Tests cover:**
- Valid temperature adjustments
- Temperature range limits (50-90°F)
- Mode switching (heat/cool/auto/off)
- Fan control (on/off)
- Input validation
- Error handling

All 52 total unit tests pass (35 core + 17 control).

## Performance Impact

**Minimal Overhead:**
- Control endpoints: ~1ms response time
- No polling (event-driven)
- Thread-safe state updates
- No additional memory usage

## Comparison with E-ink Display

| Feature | Web Interface | E-ink Display |
|---------|---------------|---------------|
| **Control** | ✅ Full control | ❌ Read-only |
| **Temp Adjust** | ✅ +/− buttons | ❌ No |
| **Mode Switch** | ✅ 4 modes | ❌ No |
| **Fan Control** | ✅ Toggle | ❌ No |
| **Remote Access** | ✅ Any device | ❌ Physical only |
| **Response** | Instant | N/A |

**Use Both:** Web interface for control/testing, e-ink for permanent display!

## Related Documentation

- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Complete web interface guide
- [TESTING.md](TESTING.md) - Testing procedures
- [README.md](../README.md) - Project overview
- [INSTALL.md](INSTALL.md) - Installation instructions

## Support

**Issues?**
1. Check logs: `sudo journalctl -u thermostat.service -f`
2. Verify Flask installed: `pip show Flask`
3. Test API manually: `curl http://localhost:5000/api/status`
4. Review error messages in browser console (F12)

**Safety Concerns?**
- All commands validated before execution
- Temperature limits hardcoded (50-90°F)
- Heat/cool interlock enforced
- Changes logged for audit trail
