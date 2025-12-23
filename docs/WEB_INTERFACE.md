# Web Interface Guide

## Overview

The web interface provides a browser-based dashboard for monitoring **and controlling** your thermostat from any device on your local network. Perfect for testing hardware without the e-ink display!

## Features

✅ **Real-time monitoring**
- Current system temperature
- Individual sensor readings
- HVAC status (heat/cool/fan)
- Target temperatures
- Compromised sensor alerts

✅ **Remote control**
- Adjust heating and cooling setpoints
- Switch HVAC modes (heat/cool/auto/off)
- Manual fan control
- Instant temperature adjustments

✅ **Auto-refresh** every 5 seconds

✅ **Mobile-friendly** responsive design

✅ **Local network only** (no internet required)

## Setup

### 1. Install Flask

```bash
pip install Flask==3.0.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Enable Web Interface

Edit `config.env`:

```bash
# Web Interface
WEB_INTERFACE_ENABLED=true
WEB_PORT=5000  # Default port
```

### 3. Start Thermostat

The web interface starts automatically when you run the thermostat:

```bash
python3 src/thermostat.py
```

You'll see:
```
Web interface started on port 5000
```

### 4. Access Dashboard

From any device on your network:

```
http://<raspberry-pi-ip>:5000
```

Find your Pi's IP:
```bash
hostname -I
```

## Using the Dashboard

### Monitoring Display

**System Temperature Card**
- Shows current median temperature from all valid sensors
- Large, easy-to-read display

**HVAC Status Card**
- Current mode (HEAT/COOL/AUTO/OFF)
- Active components (badges turn green when ON)
- Shows heat, cool, fan, and secondary heat status

**Target Temperatures Card**
- Heating setpoint with +/− buttons
- Cooling setpoint with +/− buttons
- Click buttons to adjust in 1°F increments

**Temperature Sensors List**
- All sensor readings
- Sensor names and current temperatures
- ⚠️ Warning icon for compromised sensors (near fireplace)
- Compromised sensors shown in red

### Control Features

**Temperature Adjustment**
1. Click **+** or **−** buttons next to target temperatures
2. Each click adjusts by 1°F
3. Valid range: 50°F - 90°F
4. Success message confirms change
5. Dashboard updates automatically

**Mode Selection**
- **OFF** - System completely off
- **HEAT** - Heating mode (maintains heating setpoint)
- **COOL** - Cooling mode (maintains cooling setpoint)
- **AUTO** - Automatic mode (switches between heating/cooling)

Click any mode button to activate. Active mode is highlighted.

**Fan Control**
- Toggle switch for manual fan control
- **ON** - Fan runs continuously
- **OFF** - Fan runs only when heating/cooling

**Safety Features**
- Temperature limits enforced (50-90°F)
- Invalid inputs rejected with error messages
- All changes logged for troubleshooting
- Heat and cool never run simultaneously

### Auto-Refresh

- Dashboard updates every 5 seconds automatically
- "Last updated" timestamp shows freshness
- Control changes appear immediately after confirmation
- Error messages appear if connection is lost

## Configuration Options

### Change Port

If port 5000 is already in use:

```bash
WEB_PORT=8080  # Or any available port
```

### Disable Web Interface

To run without web interface (saves memory):

```bash
WEB_INTERFACE_ENABLED=false
```

## Firewall Configuration

If you can't access from other devices, open the port:

```bash
sudo ufw allow 5000/tcp
# Or for custom port:
sudo ufw allow 8080/tcp
```

## Testing Without Hardware

You can test the web interface without connecting to sensors:

```bash
cd src
python3 web_interface.py
```

This runs in standalone mode with mock data on http://localhost:5000

## Network Access

### Same Device
```
http://localhost:5000
http://127.0.0.1:5000
```

### From Computer on Network
```
http://192.168.1.100:5000  # Replace with your Pi's IP
```

### From Phone/Tablet
- Connect to same WiFi network
- Browse to `http://<pi-ip>:5000`
- Bookmark for easy access

## Security Considerations

⚠️ **Local Network Only**
- Web interface is **read-only** (no control functions)
- Accessible only on your local network
- No authentication (trust your local network)
- No HTTPS (data not encrypted)

**Best Practices:**
- Don't expose port to internet
- Keep Pi on trusted home network
- Consider adding password protection if needed

## Troubleshooting

### "Connection refused"

**Check if thermostat is running:**
```bash
sudo systemctl status thermostat.service
```

**Check if web interface is enabled:**
```bash
grep WEB_INTERFACE_ENABLED config.env
```

**Check Pi's IP:**
```bash
hostname -I
```

### "Port already in use"

Change the port in `config.env`:
```bash
WEB_PORT=8080
```

### Dashboard shows "--" or "No data"

**Thermostat hasn't started yet:**
- Wait 30-60 seconds for first sensor reading

**Check logs:**
```bash
sudo journalctl -u thermostat.service -f
```

### Dashboard shows stale data

**Check "Last updated" timestamp**
- Should update every 30 seconds
- If frozen, thermostat may have crashed

**Restart service:**
```bash
sudo systemctl restart thermostat.service
```

### Can't access from phone/tablet

**Verify same network:**
```bash
# On Pi
hostname -I

# On phone, check WiFi settings for IP subnet
# Should be similar (e.g., both 192.168.1.x)
```

**Check firewall:**
```bash
sudo ufw status
sudo ufw allow 5000/tcp
```

### Control commands not working

**Check Flask is installed:**
```bash
pip show Flask
```

**Check logs for errors:**
```bash
sudo journalctl -u thermostat.service -f
```

**Verify control callback is set:**
- Look for "Control command received" in logs when you click buttons

**Clear browser cache:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

### Temperature won't adjust

**Check range:**
- Must be between 50°F and 90°F
- Error message appears if out of range

**Check mode:**
- Some modes ignore certain setpoints (e.g., OFF mode ignores all)

**Verify in logs:**
- Each adjustment logged: "Target heat temperature set to X°F"

## Mobile Optimization

### Add to Home Screen (iOS)

1. Open dashboard in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. Now launches like an app!

### Add to Home Screen (Android)

1. Open dashboard in Chrome
2. Tap menu (⋮)
3. Select "Add to Home screen"
4. Creates app icon

## Advanced: Reverse Proxy

For HTTPS or custom domain, use Nginx:

```nginx
server {
    listen 80;
    server_name thermostat.local;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## API Endpoints

For custom integrations or automation:

### Monitoring Endpoints (GET)

**Get full status:**
```
GET /api/status
```
Returns: System temp, HVAC state, targets, sensors, compromised list

**Get sensor details:**
```
GET /api/sensors
```
Returns: Array of sensor readings with compromise status

**Get HVAC status:**
```
GET /api/hvac
```
Returns: Mode, state, target temps, system temp

### Control Endpoints (POST)

**Set target temperature:**
```
POST /api/control/temperature
Content-Type: application/json

{
  "type": "heat",  // or "cool"
  "temperature": 70.0
}
```

**Set HVAC mode:**
```
POST /api/control/mode
Content-Type: application/json

{
  "mode": "heat"  // "heat", "cool", "auto", or "off"
}
```

**Control fan:**
```
POST /api/control/fan
Content-Type: application/json

{
  "fan_on": true  // or false
}
```

**Example with curl:**
```bash
# Set heating target to 72°F
curl -X POST http://192.168.1.100:5000/api/control/temperature \
  -H "Content-Type: application/json" \
  -d '{"type":"heat","temperature":72}'

# Switch to cooling mode
curl -X POST http://192.168.1.100:5000/api/control/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"cool"}'

# Turn fan on
curl -X POST http://192.168.1.100:5000/api/control/fan \
  -H "Content-Type: application/json" \
  -d '{"fan_on":true}'
```

## Performance

- **Memory usage:** ~50MB additional (Flask + threads)
- **CPU usage:** Negligible (<1%)
- **Network:** ~1KB per refresh, ~200 bytes per control command
- **Recommended:** Raspberry Pi 3B or newer

## Security Considerations

⚠️ **Important:** The web interface allows full control of your HVAC system.

**Built-in Safety:**
- Temperature limits enforced (50-90°F)
- Heat/cool interlock prevents simultaneous operation
- All commands logged for audit trail
- Invalid inputs rejected

**Network Security:**
- Web interface binds to all interfaces (0.0.0.0) by default
- Accessible from any device on local network
- **Do not expose port to internet** without authentication
- Consider firewall rules to limit access:
  ```bash
  # Only allow from specific devices
  sudo ufw allow from 192.168.1.0/24 to any port 5000
  ```

**Recommended Security:**
- Keep Raspberry Pi on trusted home network only
- Use strong WiFi password (WPA3)
- Regularly update Raspberry Pi OS
- Monitor logs for suspicious activity
- Consider adding HTTP Basic Auth for additional protection

**Future Security Enhancements:**
- User authentication
- HTTPS/TLS encryption
- API keys for automation
- Rate limiting

## Future Enhancements

Potential features for future development:
- Historical temperature graphs
- Schedule/programming (time-based setpoints)
- Email/push notifications for alerts
- Integration with Home Assistant or other platforms
- Multiple user accounts with permissions
- Away/vacation mode
- Weather-based adjustments

## Comparison: Web vs E-ink Display

| Feature | Web Interface | E-ink Display |
|---------|---------------|----------------|
| **Access** | Any device on network | Physical location only |
| **Updates** | Real-time (5s refresh) | Periodic (~60s) |
| **Controls** | ✅ Full control (temp, mode, fan) | ❌ Display only |
| **Power** | ~50MB RAM | Negligible |
| **Hardware** | None (software only) | $20-30 HAT |
| **Setup** | `pip install Flask` | SPI configuration |
| **Mobile** | ✅ Phone/tablet friendly | ❌ N/A |
| **Testing** | ✅ Perfect for dev/testing | ⚠️ Requires physical access |
| **Remote** | ✅ Yes (local network) | ❌ Must be near Pi |

**Recommendation:** Use web interface for initial testing and development, add e-ink display later for permanent installation if desired. Both can run simultaneously!
|---------|--------------|---------------|
| Cost | Free (software) | ~$20 hardware |
| Installation | No wiring | HAT connection |
| Accessibility | Any device | At thermostat |
| Updates | 5 seconds | 60 seconds |
| Mobile | ✅ Yes | ❌ No |
| Always visible | ❌ No | ✅ Yes |
| Power | +50MB RAM | Minimal |

**Recommendation:** Use both! E-ink for at-a-glance status, web for detailed monitoring and testing.

## Support

Having issues? Check:
1. [README.md](../README.md) - Installation guide
2. [docs/INSTALL.md](INSTALL.md) - Detailed setup
3. System logs: `sudo journalctl -u thermostat.service`
4. Flask logs in console output

---

**Quick Start Command:**
```bash
# Enable web interface
echo "WEB_INTERFACE_ENABLED=true" >> config.env

# Install Flask
pip install Flask

# Start thermostat
python3 src/thermostat.py

# Access dashboard
# http://<pi-ip>:5000
```
