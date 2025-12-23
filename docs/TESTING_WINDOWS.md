# Running Unit Tests on Windows

## Prerequisites

1. **Python 3.9+** installed
2. **Project dependencies** (only Pillow and python-dotenv needed for tests)

## Setup

```powershell
# Navigate to project directory
cd c:\Users\dareist\source\repos\thermostat

# Install test dependencies
python -m pip install pytest pytest-cov Pillow python-dotenv
```

## Run Tests

```powershell
# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_thermostat_unit.py -v

# Run specific test
python -m pytest tests/unit/test_thermostat_unit.py::TestThermostatController::test_hvac_state_safety_heat_and_cool -v
```

## View Coverage Report

After running tests with `--cov-report=html`:

```powershell
# Open in default browser
Start-Process htmlcov\index.html
```

## Expected Output

```
tests/unit/test_thermostat_unit.py::TestSensorReading::test_sensor_reading_creation PASSED
tests/unit/test_thermostat_unit.py::TestThermostatController::test_initialization PASSED
tests/unit/test_thermostat_unit.py::TestThermostatController::test_calculate_system_temperature_median PASSED
...
tests/unit/test_display_unit.py::TestThermostatDisplay::test_initialization PASSED
tests/unit/test_display_unit.py::TestThermostatDisplay::test_create_display_image_basic PASSED
...

======================== XX passed in X.XXs ========================
```

## Troubleshooting

### "No module named pytest"

Install pytest:
```powershell
python -m pip install pytest pytest-cov
```

### "No module named PIL"

Install Pillow:
```powershell
python -m pip install Pillow
```

### Import Errors

Ensure you're running from project root:
```powershell
cd c:\Users\dareist\source\repos\thermostat
python -m pytest tests/unit/
```

## VS Code Integration

1. Install **Python** extension (ms-python.python)
2. Install **Python Test Explorer** extension
3. Open Command Palette (`Ctrl+Shift+P`)
4. Select: `Python: Configure Tests`
5. Choose: `pytest`
6. Select: `tests/unit` directory
7. Tests appear in Testing sidebar (beaker icon)

## Continuous Integration

Tests run automatically on GitHub via Actions when:
- Pushing to main branch
- Creating pull requests

See: `.github/workflows/tests.yml`

## Next Steps

After unit tests pass locally:
1. Deploy to Raspberry Pi
2. Run hardware integration tests:
   - `python tests/test_sensors.py`
   - `python tests/test_relays.py`
   - `python tests/test_display.py`
