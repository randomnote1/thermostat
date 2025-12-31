# Installation and Setup Guide

This guide walks through setting up the Raspberry Pi thermostat from scratch.

## Pre-Installation Checklist

- [ ] Raspberry Pi 3B
- [ ] MicroSD card (16GB+)
- [ ] Ethernet cable
- [ ] All parts ordered (see README.md)
- [ ] Old thermostat wiring documented/photographed

## Step-by-Step Installation

### 1. Prepare SD Card

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert MicroSD card into computer
3. Open Raspberry Pi Imager
4. Click "Choose OS" → "Raspberry Pi OS (other)" → "Raspberry Pi OS Lite (64-bit)"
5. Click "Choose Storage" → Select your SD card
6. Click gear icon (⚙️) for advanced options:
   - Set hostname: `thermostat`
   - Enable SSH (password authentication)
   - Set username: `pi` and password: (your choice)
   - Configure wireless LAN: **Disabled** (leave blank)
   - Set timezone and keyboard layout
7. Click "Write" and wait for completion

### 2. First Boot

1. Insert SD card into Raspberry Pi
2. Connect Ethernet cable
3. Connect power supply (temporary USB power supply for setup)
4. Wait 2-3 minutes for first boot
5. Find IP address:
   - Check your router's DHCP client list
   - Or use: `ping thermostat.local`
6. Connect via SSH:
   ```bash
   ssh pi@thermostat.local
   ```

### 3. System Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Set timezone (adjust for your location)
sudo timedatectl set-timezone America/New_York

# Disable WiFi
sudo rfkill block wifi

# Edit boot config (path changed in recent Raspberry Pi OS)
sudo nano /boot/firmware/config.txt
```

Add to `/boot/firmware/config.txt`:
```
# Disable WiFi and Bluetooth
dtoverlay=disable-wifi
dtoverlay=disable-bt

# Enable 1-Wire for temperature sensors
dtoverlay=w1-gpio,gpiopin=4

# Enable SPI for display
dtparam=spi=on
```

**Save and exit nano:**
- Press `Ctrl+O` (WriteOut) to save
- Press `Enter` to confirm filename
- Press `Ctrl+X` to exit

Reboot:
```bash
sudo reboot
```

### 4. Install Dependencies

```bash
# Reconnect after reboot
ssh pi@thermostat.local

# Install system packages
sudo apt install -y python3 python3-pip python3-dev python3-venv \
    python3-pil python3-numpy git \
    python3-rpi.gpio python3-gpiozero python3-spidev

# Add pi user to GPIO groups
sudo usermod -a -G gpio,spi,i2c pi

# Log out and back in for group changes to take effect
exit
ssh pi@thermostat.local
```

### 5. Clone Repository

```bash
# If using git:
cd ~
git clone https://github.com/yourusername/thermostat.git
cd thermostat

# Or manually copy files via SCP from your computer:
# mkdir -p ~/thermostat
# scp -r /path/to/thermostat/* pi@thermostat.local:~/thermostat/
# cd ~/thermostat
```

### 6. Set Up Python Environment

```bash
cd ~/thermostat

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Hardware Assembly

#### Connect DS18B20 Sensors

1. **Prepare sensors:**
   - Connect 4.7kΩ pull-up resistor between 3.3V and GPIO 4
   - Wire all sensors in parallel:
     - All RED wires → 3.3V (Pin 1)
     - All BLACK wires → Ground (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
     - All YELLOW wires → GPIO 4 (Pin 7)

2. **Label each sensor:**
   ```bash
   # List detected sensors
   ls /sys/bus/w1/devices/
   
   # Read from specific sensor to identify it
   cat /sys/bus/w1/devices/28-xxxxxxxxxx/w1_slave
   ```
   
   - Touch sensor to warm it up and watch which ID changes temperature
   - Label each sensor with masking tape: "Living Room - 28-xxxx"

#### Connect Relay Board

```
Pi GPIO          Relay Board
--------         -----------
GPIO 17 (Pin 11) → IN1 (Heat)
GPIO 27 (Pin 13) → IN2 (Cool)
GPIO 22 (Pin 15) → IN3 (Fan)
GPIO 23 (Pin 16) → IN4 (Heat2)
5V (Pin 2)       → VCC
GND (Pin 6)      → GND
```

#### Install E-Ink Display HAT

- Carefully align 40-pin HAT connector
- Press firmly to seat all pins
- No individual wiring needed (HAT connects directly)

### 8. Test Components

```bash
cd ~/thermostat
source venv/bin/activate

# Test sensors
python3 tests/test_sensors.py

# Test relays (interactive mode)
python3 tests/test_relays.py --interactive

# Test display
python3 tests/test_display.py
```

### 9. Configure System

```bash
# Copy example config
cp config/config.example.env config.env

# Edit with your sensor IDs
nano config.env
```

**Nano editor commands:**
- Use arrow keys to navigate
- Press `Ctrl+O` to save, then `Enter` to confirm
- Press `Ctrl+X` to exit

Update these values:
- `SENSOR_LIVING_ROOM=` (use actual sensor ID from step 7)
- `SENSOR_KITCHEN=` (use actual sensor ID)
- etc.
- `TARGET_TEMP_HEAT=68.0` (your desired temperature)
- `MONITORED_SENSORS=SENSOR_FIREPLACE_ROOM` (sensors to watch for anomalies)

### 10. Test Thermostat Software

```bash
# Run manually first to test
cd ~/thermostat
source venv/bin/activate
python3 src/thermostat.py
```

Watch the output for 5-10 minutes:
- Verify all sensors are read
- Check HVAC logic (don't connect to actual HVAC yet!)
- Press Ctrl+C to stop

### 11. HVAC Connection

⚠️ **DANGER: 24VAC - Turn off breaker first!**

1. **Document existing wiring:**
   - Take photos of current thermostat
   - Label each wire before disconnecting

2. **Identify wires:**
   - R (red) - 24VAC power
   - C (blue/black) - 24VAC common
   - W (white) - Heat call
   - Y (yellow) - Cool call
   - G (green) - Fan call
   - W2 (brown) - Secondary heat (if present)

3. **Wire to relay board:**
   ```
   HVAC Wire → Relay Board Terminal
   ---------   ---------------------
   R         → Common terminal on all relays
   W         → Relay 1 NO (Normally Open)
   Y         → Relay 2 NO
   G         → Relay 3 NO
   W2        → Relay 4 NO
   C         → Connect to power supply ground reference
   ```

4. **Test with multimeter:**
   - Verify 24VAC between R and C
   - Test relay switching (measure voltage across NO contacts)

5. **Power Raspberry Pi from HVAC:**
   - Connect R and C to AC-DC converter input
   - Connect converter 5V output to Pi USB power

### 12. Install as Service

```bash
# Copy service file
sudo cp systemd/thermostat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start at boot)
sudo systemctl enable thermostat.service

# Start service now
sudo systemctl start thermostat.service

# Check status
sudo systemctl status thermostat.service

# View logs
sudo journalctl -u thermostat.service -f
```

### 13. Monitoring

```bash
# View live logs
sudo journalctl -u thermostat.service -f

# Check service status
sudo systemctl status thermostat.service

# Restart service
sudo systemctl restart thermostat.service

# Stop service
sudo systemctl stop thermostat.service
```

## Troubleshooting

See main [README.md](README.md#troubleshooting) for detailed troubleshooting steps.

### Quick Checks

**Sensors not detected:**
```bash
lsmod | grep w1           # Check if w1 modules loaded
ls /sys/bus/w1/devices/   # Check for sensor devices
```

**Display not working:**
```bash
ls /dev/spi*              # Check if SPI enabled
# Should see: /dev/spidev0.0 and /dev/spidev0.1
```

**HVAC not responding:**
- Verify 24VAC between R and C with multimeter
- Check relay LEDs light up when GPIO activated
- Test HVAC manually (jumper R to W wire → heat should activate)

## Next Steps

1. Monitor system for 24-48 hours
2. Tune anomaly detection thresholds in config.env
3. Adjust temperature setpoints as needed
4. Consider adding web interface (future enhancement)

## Maintenance

- Check logs weekly: `sudo journalctl -u thermostat.service --since "7 days ago"`
- Update system monthly: `sudo apt update && sudo apt upgrade`
- Clean e-ink display quarterly (soft cloth, no liquids)
- Replace SD card yearly (flash memory wears out)

## Backup Configuration

```bash
# Backup config from Pi
scp pi@thermostat.local:~/thermostat/config.env ~/thermostat-backup.env

# Backup to Pi
scp ~/thermostat-backup.env pi@thermostat.local:~/thermostat/config.env
```
