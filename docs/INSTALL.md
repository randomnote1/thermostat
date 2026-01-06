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
git clone https://github.com/randomnote1/thermostat.git
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

**DS18B20 Pinout (TO-92 Package):**

When looking at the sensor with the **flat side facing you**, the three pins from left to right are:

```
    Front View (flat side facing you):
    
         Flat side
    ┌───────────┐
    │ DS18B20   │
    │           │
    └──┬──┬──┬──┘
       │  │  │
       1  2  3
     GND DATA VDD
      │   │   │
   BLACK YELLOW RED
```

- **Pin 1 (Left)**: GND (Ground) → **BLACK wire**
- **Pin 2 (Middle)**: DATA (1-Wire signal) → **YELLOW wire**  
- **Pin 3 (Right)**: VDD (Power, 3.3V) → **RED wire**

**Raspberry Pi GPIO Pin Layout:**

```
    Raspberry Pi 40-Pin Header (view from top, SD card on right):
    
    3.3V (Pin 1)  ●────────● (Pin 2)  5V        ← Row closest to board edge
       ↓ RED here
    GPIO 2        ●────────● (Pin 4)  5V
    GPIO 3        ●────────● (Pin 6)  GND
                              ↑ BLACK here
    GPIO 4        ●────────● (Pin 8)  GPIO 14
  ↑ Pin 7                            
  YELLOW here                        
                            
    GND           ●────────● (Pin 10) GPIO 15
    GPIO 17       ●────────● (Pin 12) GPIO 18
    ...continuing down to pin 40
```

1. **Prepare sensors:**
   - Connect 4.7kΩ pull-up resistor between 3.3V (red wire) and GPIO 4 (yellow DATA wire) - one resistor for entire bus
   - Wire all sensors in parallel:
     - All RED wires (Pin 3/VDD) → 3.3V (Pi GPIO Pin 1)
     - All BLACK wires (Pin 1/GND) → Ground (Pi GPIO Pin 6, 9, 14, 20, 25, 30, 34, or 39)
     - All YELLOW wires (Pin 2/DATA) → GPIO 4 (Pi GPIO Pin 7)

**Connection Methods:**

**Option A: Direct GPIO Header Connection (Simple)**
- Use female-to-female jumper wires or crimp connectors
- Plug directly onto GPIO pins 1, 6, and 7
- Less secure, may need hot glue to prevent disconnection

**Option B: Screw Terminal Board (RECOMMENDED - 52Pi EP-0129)**

**ASCII Diagram - Side View:**

```
    Viewing from the side (cross-section):
    
    ╔═══════════════════════════════════════════╗
    ║    Raspberry Pi 40-pin GPIO header       ║  ← Pi's male pins point UP
    ║         (male pins sticking up)          ║
    ╚═══╤═══╤═══╤═══╤═══╤═══╤═══╤═══╤═════════╝
        │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 ...     ← Pin numbers
        ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓
    ╔═══╧═══╧═══╧═══╧═══╧═══╧═══╧═══╧═════════╗
    ║ 40-pin female header (on bottom of HAT) ║  ← Screw terminal board
    ╠═════════════════════════════════════════╣    plugs onto these pins
    ║                                         ║
    ║  [●●●●●] ← LED indicators               ║
    ║                                         ║
    ║  SCREW TERMINAL BOARD (52Pi EP-0129)    ║
    ║                                         ║
    ║  Terminals face OUTWARD (toward you):  ║
    ║                                         ║
    ║  ┌──┬──┬──┬──┬──┬──┬──┬──┐            ║
    ║  │ 1│ 2│ 3│ 4│ 5│ 6│ 7│ 8│            ║
    ║  └──┴──┴──┴──┴──┴──┴──┴──┘            ║
    ║   ▲     ▲                 ▲     ▲      ║
    ║   │     │                 │     │      ║
    ║  3V3   5V               GND   GP4      ║
    ╚═════════════════════════════════════════╝
         │                       │     │
         │                       │     └─ YELLOW wires (data)
         │                       └─ BLACK wires (ground)
         └─ RED wires (power) + one resistor leg
                                      
    4.7kΩ resistor: Terminal 1 (3V3) ←→ Terminal 7 (GP4)
```

**Top-Down View (looking down at board as you see it):**

```
    Board shown from above (terminals facing you):
    
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                PWR ◄─┐ GPIO      ║
    ║  SCREW TERMINAL HAT                                USB  STATUS   ║
    ║                                                                  ║
    ║  Row 1 (Pins 1-10)                                               ║
    ║  ╔════╦════╦════╦════╦════╦════╦════╦════╦════╦════╗             ║
    ║  ║+3V3║GND ║IO17║IO18║MOSI║MISO║SCLK║ CE0║ CE1║GND ║    [●]      ║
    ║  ╠════╬════╬════╬════╬════╬════╬════╬════╬════╬════╣    [●]      ║
    ║  ║  1 ║  2 ║  3 ║  4 ║  5 ║  6 ║  7 ║  8 ║  9 ║ 10 ║    [●]      ║
    ║  ╚════╩════╩════╩════╩════╩════╩════╩════╩════╩════╝    [●]      ║
    ║    ▲                                                    [●]  L   ║
    ║    └─ RED wires + resistor leg (3.3V power)             [●]  E   ║
    ║                                                         [●]  D   ║
    ║  Row 2 (Pins 11-20)                                     [●]      ║
    ║  ╔════╦════╦════╦════╦════╦════╦════╦════╦════╦════╗    [●]  S   ║
    ║  ║+3V3║GND ║ TXD║ RXD║IO24║IO25║ IO5║ IO6║IO16║GND ║    [●]  T   ║
    ║  ╠════╬════╬════╬════╬════╬════╬════╬════╬════╬════╣    [●]  A   ║
    ║  ║ 11 ║ 12 ║ 13 ║ 14 ║ 15 ║ 16 ║ 17 ║ 18 ║ 19 ║ 20 ║    [●]  T   ║
    ║  ╚════╩════╩════╩════╩════╩════╩════╩════╩════╩════╝    [●]  U   ║
    ║         ▲                                               [●]  S   ║
    ║         └─ Alternative GND (BLACK wires)                [●]      ║
    ║                                                         [●]  I   ║
    ║                                                         [●]  N   ║
    ║  Row 3 (Pins 21-30)                                     [●]  D   ║
    ║  ╔════╦════╦════╦════╦════╦════╦════╦════╦════╦════╗    [●]  I   ║
    ║  ║ +5V║GND ║IO23║IO22║IO5D║ID5C║IO12║IO20║IO19║GND ║    [●]  C   ║
    ║  ╠════╬════╬════╬════╬════╬════╬════╬════╬════╬════╣    [●]  A   ║
    ║  ║ 21 ║ 22 ║ 23 ║ 24 ║ 25 ║ 26 ║ 27 ║ 28 ║ 29 ║ 30 ║    [●]  T   ║
    ║  ╚════╩════╩════╩════╩════╩════╩════╩════╩════╩════╝    [●]  O   ║
    ║         ▲                                       ▲       [●]  R   ║
    ║         └─ Alternative GND (BLACK wires)        └─ Alt  [●]  S   ║
    ║                                                    GND  [●]      ║
    ║  Row 4 (Pins 31-40)                                     [●]      ║
    ║  ╔════╦════╦════╦════╦════╦════╦════╦════╦════╦════╗    [●]      ║
    ║  ║ +5V║GND ║ SDA║ SCL║ IO4║IO27║IO21║IO13║IO26║GND ║    [●]      ║
    ║  ╠════╬════╬════╬════╬════╬════╬════╬════╬════╬════╣    [●]      ║
    ║  ║ 31 ║ 32 ║ 33 ║ 34 ║ 35 ║ 36 ║ 37 ║ 38 ║ 39 ║ 40 ║    [●]      ║
    ║  ╚════╩════╩════╩════╩════╩════╩════╩════╩════╩════╝    [●]      ║
    ║         ▲              ▲                        ▲       [●]  ↑   ║
    ║         └─ Alternative └─ YELLOW wires +        └─ Alt  [●]      ║
    ║            GND            resistor leg             GND  [●]      ║
    ║                           (GPIO 4)                               ║
    ╚══════════════════════════════════════════════════════════════════╝
```

**IMPORTANT - Terminal Locations for DS18B20:**

Based on the physical board layout shown above:
- **+3V3** (3.3V power): Terminal #1 in Row 1 → Connect RED wires here
- **GND** (Ground): Terminal #2, #12, #22, #30, #32, or #40 → Connect BLACK wires (any GND works)
- **IO4** (GPIO 4): Terminal #35 in Row 4 → Connect YELLOW wires here
- **4.7kΩ Resistor**: One leg in terminal #1 (+3V3), other leg in terminal #35 (IO4)

**Alternative (may vary by board revision):**
Some boards may have different terminal arrangements. Look for these labels printed on YOUR board:
- Find "+3V3" label → RED wires
- Find "GND" label → BLACK wires  
- Find "IO4" label on Row 4 (Terminal #35) → YELLOW wires

The board label at Row 2 position 18 is "IO6" (not used for DS18B20).
The GPIO 4 connection is at Row 4 position 35, labeled "IO4".

**Terminal Labels (what you'll see printed on the board):**

The 52Pi EP-0129 board has 40 screw terminals arranged in 4 rows of 10.
Looking at your board with the 40-pin header at the top:

```
Row 1 (Terminals 1-10):
+3V3, GND, IO17, IO18, MOSI, MISO, SCLK, CE0, CE1, GND
  ▲                                                   ▲
  RED wires + resistor                               Alternative GND

Row 2 (Terminals 11-20):
+3V3, GND, TXD, RXD, IO24, IO25, IO5, IO6, IO16, GND
                                      ▲
                                   (Not used for DS18B20)

Row 3 (Terminals 21-30):
+5V, GND, IO23, IO22, IO5D, ID5C, IO12, IO20, IO19, GND

Row 4 (Terminals 31-40):
+5V, GND, SDA, SCL, IO4, IO27, IO21, IO13, IO26, GND
                    ▲
                 YELLOW wires + resistor (GPIO 4)
```

**Key Terminal Locations:**
- Terminal #1 (Row 1): "+3V3" → RED wires + one resistor leg
- Terminal #2 (Row 1): "GND" → BLACK wires
- Terminal #35 (Row 4): "IO4" → YELLOW wires + other resistor leg

**Board Orientation:** 
- The screw terminal board sits on top of the Raspberry Pi GPIO pins
- The screw terminals face OUTWARD (toward you, away from the Pi)
- LEDs face upward (visible when installed)
- White pin label sticker shows pin numbers (look for "1" in corner near SD card edge)

**Physical Installation:**
1. Align board's 40-pin female header with Pi's 40-pin male header
2. "Pin 1" on board aligns with "Pin 1" on Pi (corner near SD card slot)
3. Press down firmly to fully seat the connector

**Wiring Instructions:**

```
Step 1: Strip and prepare all sensor wires
   
Step 2: Connect RED wires
        └─ All red wires go into terminal #1 (labeled "+3V3" in Row 1)
        └─ Tighten screw to secure
   
Step 3: Connect BLACK wires  
        └─ All black wires go into any GND terminal (e.g., terminal #2, #12, #22, or #32)
        └─ Tighten screw to secure
   
Step 4: Connect YELLOW wires
        └─ All yellow wires go into terminal #35 (labeled "IO4" in Row 4)
        └─ Tighten screw to secure
   
Step 5: Install pull-up resistor (4.7kΩ)
        └─ One resistor leg goes into terminal #1 (with red wires)
        └─ Other resistor leg goes into terminal #35 (with yellow wires)
        └─ Tighten both screws to secure resistor legs
```

**Physical Tips:**
- Terminals are numbered 1-40 across 4 rows of 10 terminals each
- Row 1: Terminals 1-10 (leftmost is #1)
- Row 2: Terminals 11-20
- Row 3: Terminals 21-30
- Row 4: Terminals 31-40
- "+3V3" terminal is #1 in Row 1
- "IO4" terminal is #35 in Row 4 (this connects to GPIO 4 on the Pi)
- "IO6" terminal is #18 in Row 2 (not used for DS18B20)

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
nano config.env  # Edit to match your hardware

# Create log file with proper permissions
sudo touch /var/log/thermostat.log
sudo chown pi:pi /var/log/thermostat.log
sudo chmod 644 /var/log/thermostat.log

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
