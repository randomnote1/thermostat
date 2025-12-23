# Project Structure

```
thermostat/
├── .github/
│   └── copilot-instructions.md    # GitHub Copilot development guidelines
│
├── .vscode/                        # VS Code workspace settings
│
├── config/
│   └── config.example.env         # Configuration template
│
├── docs/
│   ├── INSTALL.md                 # Complete installation guide
│   ├── PARTS_LIST.md              # Shopping list with part numbers
│   ├── SENSOR_MOUNTING.md         # Detailed sensor installation guide
│   └── VSCODE_EXTENSIONS.md       # Recommended VS Code extensions
│
├── src/
│   ├── thermostat.py              # Main application and control logic
│   └── display.py                 # E-ink display management
│
├── systemd/
│   └── thermostat.service         # Systemd service configuration
│
├── tests/
│   ├── __init__.py
│   ├── unit/                       # Unit tests (no hardware)
│   │   ├── __init__.py
│   │   ├── test_thermostat_unit.py
│   │   └── test_display_unit.py
│   ├── test_sensors.py            # Hardware: DS18B20 sensor testing
│   ├── test_relays.py             # Hardware: Relay board testing
│   └── test_display.py            # Hardware: E-ink display testing
│
├── .gitignore                      # Git ignore rules
├── README.md                       # Project overview and quick start
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
└── STRUCTURE.md                    # This file

```

## Directory Purposes

### `/src`
Main application code that runs as the thermostat system.
- **thermostat.py**: Core control loop, sensor reading, anomaly detection, HVAC control
- **display.py**: E-ink display rendering and updates

### `/tests`
Hardware validation scripts and unit tests.

**Unit tests** (tests/unit/):
- Run on any development machine
- No hardware dependencies (mocked)
- Fast execution
- Test core logic in isolation
- Run with: `pytest tests/unit/`

**Integration tests**:
- Run on Raspberry Pi only
- Test actual hardware
- Verify physical connections
- Interactive troubleshooting

### `/config`
Configuration files (not committed to git).
- Copy `config.example.env` to `config.env` and customize
- Contains sensor IDs, GPIO pins, temperature setpoints, timing parameters

### `/systemd`
System service definitions for auto-start on boot.
- Install to `/etc/systemd/system/` on the Raspberry Pi

### `/docs`
Comprehensive documentation:
- **INSTALL.md**: Step-by-step setup from blank SD card to running system
- **PARTS_LIST.md**: Complete shopping list with Amazon/DigiKey part numbers
- **SENSOR_MOUNTING.md**: Detailed wiring and mounting instructions
- **VSCODE_EXTENSIONS.md**: Recommended development environment setup
- **TESTING.md**: Unit testing guide and best practices
- **TESTING_WINDOWS.md**: Windows-specific testing instructions

### `/.github`
GitHub-specific files including Copilot instructions for AI-assisted development.

## Key Files

### `README.md`
Project overview, architecture, quick start guide, and troubleshooting.

### `requirements.txt`
Python package dependencies:
- RPi.GPIO
- w1thermsensor
- Pillow
- python-dotenv
- waveshare-epd

### `.gitignore`
Excludes from git:
- `config.env` (sensitive configuration)
- `*.pyc`, `__pycache__/` (Python bytecode)
- `venv/` (virtual environment)
- Log files

## Typical Development Workflow

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd thermostat
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Run unit tests (development machine)**
   ```bash
   pytest tests/unit/ -v
   ```

4. **Configure**
   ```bash
   cp config/config.example.env config.env
   nano config.env
   ```

5. **Deploy to Raspberry Pi**
   ```bash
   scp -r . pi@raspberrypi:/home/pi/thermostat
   ```

6. **Test hardware (on Raspberry Pi)**
   ```bash
   python3 tests/test_sensors.py
   python3 tests/test_relays.py
   python3 tests/test_display.py
   ```

7. **Run application**
   ```bash
   python3 src/thermostat.py
   ```

8. **Install service**
   ```bash
   sudo cp systemd/thermostat.service /etc/systemd/system/
   sudo systemctl enable thermostat.service
   sudo systemctl start thermostat.service
   ```

## Deployment Structure on Raspberry Pi

```
/home/pi/thermostat/
├── venv/                    # Python virtual environment
├── src/
│   ├── thermostat.py
│   └── display.py
├── config.env               # Active configuration (not in git)
├── thermostat.log           # Application logs
└── tests/
    └── ...
```

Service runs as user `pi` from `/home/pi/thermostat/`.

## Adding New Features

When extending the project:

1. **New hardware component**: Add test script in `tests/`
2. **New configuration option**: Update `config/config.example.env`
3. **Installation changes**: Update `docs/INSTALL.md`
4. **Part requirements**: Update `docs/PARTS_LIST.md`
5. **Core functionality**: Modify `src/thermostat.py` or `src/display.py`

Always follow the guidelines in `.github/copilot-instructions.md` for consistent code style and safety practices.
