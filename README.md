# Raspberry Pi Multi-Zone Thermostat

A custom thermostat system using Raspberry Pi 3B with multiple temperature sensors and intelligent zone management to solve the fireplace proximity issue.

## Project Overview

This thermostat system allows you to:
- Monitor temperature across multiple rooms
- Intelligently ignore sensors near active heat sources (fireplace)
- Control standard HVAC systems (heating, cooling, secondary heat stage)
- **Control remotely via web interface** (adjust temps, switch modes, control fan)
- Display information on an e-ink screen (optional)
- Operate completely offline

## Table of Contents

1. [Hardware Components](#hardware-components)
2. [System Architecture](#system-architecture)
3. [Software Stack](#software-stack)
4. [Installation Guide](#installation-guide)
5. [Testing](#testing)
6. [Wiring Diagrams](#wiring-diagrams)
7. [Configuration](#configuration)
8. [Safety Considerations](#safety-considerations)
9. [Troubleshooting](#troubleshooting)

## Hardware Components

### Required Parts

#### Core Components
- **Raspberry Pi 3B** (already have)
- **MicroSD Card**: 16GB minimum, Class 10 (for OS and software)
- **Power Supply**: 24VAC to 5VDC converter
  - Recommended: MEAN WELL IRM-03-5 (5V 600mA, AC-DC converter)
  - Or: Isolated 24VAC to 5VDC buck converter with 2.5A+ output
  - **Important**: Must be isolated and rated for your HVAC voltage

#### Display
- **Waveshare 2.13" E-Ink Display HAT** (250x122 pixels)
  - Model: 2.13inch e-Paper HAT (B) with Red/Black/White
  - Or: 2.7" or 4.2" for larger display
  - Connects via SPI to Raspberry Pi GPIO

#### Temperature Sensors (Choose One Approach)

**Option A: DS18B20 (Recommended for beginners)**
- **Quantity**: 4-6 sensors (one per room)
- **Type**: DS18B20 Waterproof Digital Temperature Sensor
- **Connection**: 1-Wire protocol (can run all on same 3-wire bus)
- **Advantages**: Simple wiring, long cable runs possible (up to 100m)
- **Cost**: ~$3-5 per sensor

**Option B: BME280 (Advanced - includes humidity)**
- **Quantity**: 4-6 sensors
- **Type**: BME280 I2C Temperature/Humidity/Pressure Sensor
- **Connection**: I2C protocol (requires I2C multiplexer for multiple sensors)
- **Additional Part Needed**: TCA9548A I2C Multiplexer
- **Advantages**: Humidity sensing, more accurate
- **Cost**: ~$5-8 per sensor + $5 for multiplexer

#### HVAC Control Interface
- **Relay Board**: 4-Channel 5V Relay Module (optocoupler isolated)
  - Recommended: SainSmart 4-Channel Relay
  - Channels needed:
    - Channel 1: Heat (W wire)
    - Channel 2: Cool (Y wire)
    - Channel 3: Fan (G wire)
    - Channel 4: Secondary Heat/Emergency Heat (W2 or E wire)
- **Important**: Must be rated for 24VAC @ 1A minimum

#### Miscellaneous
- **4.7kΩ Resistor** (if using DS18B20 sensors - pull-up resistor)
- **Terminal Blocks**: For HVAC wire connections
- **Jumper Wires**: Female-to-female for prototyping
- **Enclosure**: Project box to house the Pi and electronics
- **CAT5e/CAT6 Cable**: For running sensor wires between rooms

### Estimated Total Cost

- E-ink Display: $15-30
- DS18B20 Sensors (6x): $20-30
- Relay Board: $8-12
- Power Supply: $10-15
- MicroSD Card: $8-12
- Miscellaneous (wires, resistors, terminals): $15-20
- Enclosure: $10-20

**Total: $86-139** (excluding Raspberry Pi you already have)

## System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 3B                      │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Sensor     │  │  Thermostat  │  │    HVAC      │ │
│  │   Reader     │─▶│    Logic     │─▶│  Controller  │ │
│  │   (1-Wire)   │  │  (Python)    │  │   (Relays)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                 │                   │        │
│         ▼                 ▼                   ▼        │
│  ┌──────────────────────────────────────────────────┐ │
│  │         E-Ink Display (SPI Interface)            │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
    [Temp Sensors]                          [HVAC System]
   (6x DS18B20)                             (24VAC Control)
```

### Operating Logic

1. **Sensor Reading** (every 30 seconds)
   - Read all temperature sensors
   - Store readings with timestamps
   - Calculate rate of change for each sensor

2. **Anomaly Detection** (fireplace detection)
   - If a sensor's rate of change > 3°F in 5 minutes, flag as "compromised"
   - If a sensor reads > 5°F above average of other sensors, flag as "compromised"
   - Compromised sensors are excluded from HVAC decision for 60 minutes

3. **HVAC Decision** (every 60 seconds)
   - Use median of non-compromised sensors as "system temperature"
   - Compare to setpoint with hysteresis (±0.5°F)
   - Activate appropriate relay (heat/cool)
   - Enforce minimum run times (5 min) and rest times (5 min)

4. **Display Update** (every 60 seconds)
   - Show current system temperature
   - Show setpoint
   - Show HVAC status
   - Show individual room temperatures
   - Indicate which sensors are being ignored

## Software Stack

### Operating System

**Raspberry Pi OS Lite (64-bit)** - Headless, no desktop environment
- Latest version: Debian Bookworm based
- Lightweight and stable
- Official support for Raspberry Pi hardware

### Programming Language

**Python 3** - Best choice for this project because:
- Excellent GPIO and sensor libraries
- Large Raspberry Pi community
- Easier learning curve than C/C++
- Good for both beginners and advanced users
- Better than PowerShell for embedded Linux projects

### Key Python Libraries

- `RPi.GPIO` - GPIO control
- `w1thermsensor` - DS18B20 sensor reading
- `Pillow` (PIL) - Image processing for e-ink display
- `spidev` - SPI communication for display
- `gpiozero` - Higher-level GPIO interface
- `python-dotenv` - Configuration management

## Installation Guide

**See [docs/INSTALL.md](docs/INSTALL.md) for complete step-by-step installation instructions.**

### Quick Start

```bash
# Clone repository
git clone https://github.com/randomnote1/thermostat.git ~/thermostat
cd ~/thermostat

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp config/config.example.env config.env
nano config.env  # Edit with your settings

# Test hardware
python3 tests/test_sensors.py
python3 tests/test_relays.py

# Run thermostat
python3 src/thermostat.py
```

For detailed hardware setup, OS configuration, wiring diagrams, and systemd service installation, see the **[complete installation guide](docs/INSTALL.md)**.

## Testing

### Unit Tests (Development Machine)

Run comprehensive unit tests on any machine without hardware:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/unit/ -v

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=html
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing guide.

### Hardware Integration Tests (Raspberry Pi)

After deploying to Raspberry Pi, test hardware components:

```bash
# Test temperature sensors
python3 tests/test_sensors.py

# Test relays
python3 tests/test_relays.py

# Test e-ink display
python3 tests/test_display.py
```

## Wiring Diagrams

### DS18B20 Temperature Sensors (1-Wire)

```
Raspberry Pi GPIO 4 (1-Wire Data)
    │
    ├─── 4.7kΩ Resistor ─── 3.3V
    │
    ├─── DS18B20 #1 (Data Wire - Yellow)
    ├─── DS18B20 #2 (Data Wire - Yellow)
    ├─── DS18B20 #3 (Data Wire - Yellow)
    └─── ... (All sensors in parallel)

Each DS18B20 sensor:
    - Red Wire    → 3.3V (or 5V)
    - Black Wire  → Ground
    - Yellow Wire → GPIO 4 (with pull-up resistor)
```

### 4-Channel Relay Board

```
Raspberry Pi          →     Relay Board
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO 17 (Pin 11)      →     IN1 (Heat)
GPIO 27 (Pin 13)      →     IN2 (Cool)
GPIO 22 (Pin 15)      →     IN3 (Fan)
GPIO 23 (Pin 16)      →     IN4 (Secondary Heat)
5V (Pin 2)            →     VCC
Ground (Pin 6)        →     GND
```

### E-Ink Display (2.13" Waveshare HAT)

The Waveshare e-ink HAT connects directly to the GPIO header:
- Connects to pins 1-40 on GPIO header
- Uses SPI interface (automatically configured)
- No separate wiring needed (it's a HAT)

### HVAC System Connections

```
Thermostat Wire    Relay Board      HVAC System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R (24VAC Red)      Common Terminal  R (24VAC Power)
W (Heat)           Relay 1 (NO)     W (Heat Call)
Y (Cool)           Relay 2 (NO)     Y (Cool Call)
G (Fan)            Relay 3 (NO)     G (Fan)
W2 (2nd Stage)     Relay 4 (NO)     W2 (2nd Stage Heat)
C (Common)         Ground/Common    C (24VAC Common)
```

**Important HVAC Wiring Notes:**
1. The R (24VAC) wire connects to the COMMON terminal of all relays
2. Each relay's Normally Open (NO) contact connects to its respective HVAC wire
3. NEVER connect 24VAC directly to the Raspberry Pi
4. The C (common) wire provides the return path for 24VAC
5. Test with a multimeter: should read ~24VAC between R and C

### Power Supply

```
HVAC System                        Raspberry Pi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R (24VAC) ──┐
            ├──→ AC-DC Converter → 5VDC @ 2.5A → Pi USB Power
C (Common) ─┘    (MEAN WELL IRM-03-5)
```

## Configuration

The thermostat uses a two-tier configuration system:

### 1. Hardware Configuration (`config.env`)

Edit `config.env` in the project root to match your hardware setup:

```bash
nano config.env
```

This file contains **hardware-specific settings** that rarely change:
- GPIO pin assignments (must match your wiring)
- Sensor timing and thresholds
- HVAC safety timings
- Database and logging paths
- Initial sensor IDs (for first-run discovery)

**Important:** After initial setup, most settings (temperatures, modes, schedules) are managed via the web interface and stored in the database.

### 2. Runtime Configuration (Database)

User-facing settings are stored in `thermostat.db` and managed via the web interface:
- Target temperatures (heat/cool setpoints)
- HVAC mode (heat, cool, auto, off)
- Fan mode (auto, on, circulate)
- Schedules (time-based temperature programs)
- Sensor names and monitoring preferences

The web interface is available at `http://your-raspberry-pi-ip:5000`

### Key Configuration Settings

See `config.example.env` for detailed documentation. Critical settings include:

### Key Configuration Settings

See `config.example.env` for detailed documentation. Critical settings include:

**GPIO Pins** (BCM numbering - must match your relay board):
```bash
GPIO_RELAY_HEAT=17
GPIO_RELAY_COOL=27
GPIO_RELAY_FAN=22
GPIO_RELAY_HEAT2=23
```

**Sensor Settings** (adjust based on your fireplace behavior):
```bash
SENSOR_ANOMALY_THRESHOLD=3.0    # °F rapid change = fireplace ignition
SENSOR_DEVIATION_THRESHOLD=5.0  # °F above average = too close to fireplace
SENSOR_IGNORE_DURATION=3600     # Ignore compromised sensor for 1 hour
```

**HVAC Safety** (protect your equipment):
```bash
HVAC_MIN_RUN_TIME=300           # 5-minute minimum runtime
HVAC_MIN_REST_TIME=300          # 5-minute minimum between cycles
```

**First-Run Defaults** (database takes over after first run):
```bash
TARGET_TEMP_HEAT=68.0           # Initial heating setpoint (°F)
TARGET_TEMP_COOL=74.0           # Initial cooling setpoint (°F)
HVAC_MODE=heat                  # Initial mode
```

### Finding Your Sensor IDs

### Sensor ID Discovery

To find your DS18B20 sensor IDs:

```bash
# List all detected sensors
ls /sys/bus/w1/devices/

# Output will look like:
# 28-0000000a1b2c  28-0000000d3e4f  28-0000000g5h6i  w1_bus_master1

# Read temperature from a specific sensor
cat /sys/bus/w1/devices/28-0000000a1b2c/w1_slave
```

Label each sensor with its ID before installation!

## Safety Considerations

### Electrical Safety

⚠️ **CRITICAL: HVAC systems use 24VAC which can be dangerous**

1. **Turn off power** at the breaker before any HVAC wiring
2. **Use an isolated power supply** for the Raspberry Pi
3. **Never connect 24VAC directly to Raspberry Pi GPIO pins**
4. **Use optocoupler-isolated relays** (most relay boards have this)
5. **Verify voltage** with a multimeter before connecting
6. **Follow local electrical codes** - consider hiring an electrician

### System Safety

1. **Temperature Limits**
   - Implement emergency shutoff if any sensor reads >100°F or <32°F
   - Monitor for sensor failures (no reading in 5 minutes)

2. **HVAC Protection**
   - Enforce minimum run times (prevent short-cycling)
   - Never activate heat and cool simultaneously
   - Limit secondary heat stage to extreme conditions

3. **Backup Plans**
   - Keep your old thermostat accessible for reconnection
   - Document your original HVAC wiring before modification
   - Test in spring/fall when HVAC is less critical

### Software Safeguards

The provided code includes:
- Watchdog timer to restart on crashes
- Sensor validation and error handling
- HVAC lockouts and interlocks
- Emergency temperature limits
- Logging for troubleshooting

## Troubleshooting

### Sensors Not Detected

```bash
# Check if 1-Wire is enabled
lsmod | grep w1

# Should see: w1_gpio, w1_therm

# Check for devices
ls /sys/bus/w1/devices/

# If empty, check:
cat /boot/firmware/config.txt | grep w1-gpio
# Should see: dtoverlay=w1-gpio,gpiopin=4

# Check physical connections:
# - Pull-up resistor (4.7kΩ) between data and 3.3V
# - All ground wires connected
# - Data wires all connected to GPIO 4
```

### Relays Not Switching

```bash
# Test GPIO manually
echo "17" > /export/gpio/export
echo "out" > /sys/class/gpio/gpio17/direction
echo "1" > /sys/class/gpio/gpio17/value  # Turn on
echo "0" > /sys/class/gpio/gpio17/value  # Turn off

# Check relay board power
# - VCC should be 5V
# - GND connected

# Verify relay board type
# - Some boards are active LOW (default HIGH)
# - Check if LED lights when GPIO is LOW vs HIGH
```

### E-Ink Display Not Updating

```bash
# Check SPI is enabled
ls /dev/spi*
# Should see: /dev/spidev0.0  /dev/spidev0.1

# Enable if missing
sudo raspi-config
# Interface Options → SPI → Enable

# Check HAT is seated properly
# - All 40 pins making contact
# - No bent pins

# Test with example code
cd ~/Waveshare_example
python3 epd_2in13_V2_test.py
```

### HVAC Not Responding

1. **Verify voltage**: Multimeter between R and C should read ~24VAC
2. **Check relay switching**: LED on relay board should light up
3. **Test manually**: Remove Pi, jumper R wire to W wire → heat should activate
4. **Verify wiring**: Common (R) connects to all relay common terminals
5. **Check HVAC breaker**: Ensure furnace/air handler has power

### Python Errors

```bash
# Check logs
sudo journalctl -u thermostat.service -n 100

# Common issues:
# - Virtual environment not activated
# - Missing dependencies: pip install -r requirements.txt
# - Permission errors: sudo usermod -a -G gpio,spi,i2c pi
```

## Next Steps

1. **Review this plan** and order parts
2. **Set up the Raspberry Pi** with OS and software
3. **Test each component** individually before integration
4. **Wire the system** carefully with power OFF
5. **Run in test mode** for a few days before going live
6. **Monitor and tune** the anomaly detection settings

## Additional Resources

### Documentation Files
- [docs/INSTALL.md](docs/INSTALL.md) - Complete installation guide
- [docs/PARTS_LIST.md](docs/PARTS_LIST.md) - Detailed parts list with links
- [docs/SENSOR_MOUNTING.md](docs/SENSOR_MOUNTING.md) - Sensor installation guide
- [docs/WEB_INTERFACE.md](docs/WEB_INTERFACE.md) - Web dashboard setup and usage
- [docs/CONTROL_FEATURES.md](docs/CONTROL_FEATURES.md) - **Remote control guide**
- [docs/TESTING.md](docs/TESTING.md) - Testing procedures
- [docs/STRUCTURE.md](docs/STRUCTURE.md) - Project structure reference

### Hardware References
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [DS18B20 Datasheet](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
- [Waveshare E-Ink Documentation](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
- [HVAC Wiring Guide](https://www.youtube.com/watch?v=Lw4JYy9e-fg)

## Contributing

This is a personal project, but feel free to suggest improvements or report issues.

## License

MIT License - Use at your own risk. No warranty provided.