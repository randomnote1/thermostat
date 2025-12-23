# Unit Testing Guide

## Overview

The project includes comprehensive unit tests for core functionality. Unit tests are isolated from hardware dependencies and can run on any development machine.

## Test Structure

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_thermostat_unit.py    # Core control logic tests
│   └── test_display_unit.py       # Display management tests
├── test_sensors.py                 # Hardware integration test
├── test_relays.py                  # Hardware integration test
└── test_display.py                 # Hardware integration test
```

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-cov
```

### Run All Unit Tests

```bash
# From project root
pytest tests/unit/

# Or with verbose output
pytest tests/unit/ -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_thermostat_unit.py
pytest tests/unit/test_display_unit.py
```

### Run Specific Test

```bash
pytest tests/unit/test_thermostat_unit.py::TestThermostatController::test_hvac_state_safety_heat_and_cool
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/unit/ --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

### Run from VS Code

1. Install Python Test Explorer extension
2. Configure test framework: `pytest`
3. Tests appear in Testing sidebar
4. Click play button to run tests

## What is Tested

### `test_thermostat_unit.py`

**SensorReading Class:**
- ✅ Sensor reading creation
- ✅ Compromised flag management

**ThermostatController Class:**
- ✅ Configuration initialization
- ✅ System temperature calculation (median)
- ✅ Compromised sensor exclusion
- ✅ Sensor status tracking
- ✅ Anomaly detection (rapid change)
- ✅ Anomaly detection (deviation from average)
- ✅ Expired compromised sensor clearing
- ✅ HVAC safety (no simultaneous heat+cool)
- ✅ HVAC heating control logic
- ✅ HVAC cooling control logic
- ✅ Secondary heat activation
- ✅ Minimum run time enforcement
- ✅ Minimum rest time enforcement
- ✅ Off mode behavior
- ✅ Sensor history management
- ✅ History pruning (>30 minutes)
- ✅ Status reporting

### `test_display_unit.py`

**ThermostatDisplay Class:**
- ✅ Display initialization
- ✅ Image creation (basic)
- ✅ Image creation with sensors
- ✅ Compromised sensor marking
- ✅ Multiple HVAC states
- ✅ Long sensor name truncation
- ✅ Sensor count limiting (max 5)
- ✅ Update without hardware
- ✅ Update with default parameters
- ✅ Mock display update
- ✅ Clear display
- ✅ Sleep display
- ✅ Cleanup
- ✅ Error handling

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module>_unit.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_is_being_tested>`

### Example Test

```python
def test_calculate_system_temperature_median(self):
    """Test system temperature calculation uses median"""
    readings = [
        SensorReading('s1', 'Room1', 70.0, datetime.now()),
        SensorReading('s2', 'Room2', 72.0, datetime.now()),
        SensorReading('s3', 'Room3', 74.0, datetime.now()),
    ]
    
    temp = self.controller.calculate_system_temperature(readings)
    self.assertEqual(temp, 72.0)  # Median of [70, 72, 74]
```

### Best Practices

1. **Isolate hardware dependencies** - Use mocks for GPIO, sensors, display
2. **Test one thing per test** - Each test should verify a single behavior
3. **Use descriptive names** - Test name should explain what it tests
4. **Use setup/teardown** - Initialize common test data in `setUp()`
5. **Test edge cases** - Empty lists, None values, boundary conditions
6. **Test error handling** - Verify graceful failure
7. **Follow AAA pattern** - Arrange, Act, Assert

### Mocking Hardware

```python
# Mock GPIO
sys.modules['RPi'] = MagicMock()
sys.modules['RPi.GPIO'] = MagicMock()

# Mock sensors
sys.modules['w1thermsensor'] = MagicMock()

# Mock display
sys.modules['waveshare_epd'] = MagicMock()
```

## Continuous Integration

To add CI testing with GitHub Actions, create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run unit tests
      run: pytest tests/unit/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test vs Integration Tests

**Unit Tests** (tests/unit/):
- No hardware required
- Fast execution
- Run on any machine
- Test isolated logic
- Mock external dependencies

**Integration Tests** (test_sensors.py, test_relays.py, test_display.py):
- Require actual hardware
- Run on Raspberry Pi only
- Test hardware interaction
- Verify physical connections

## Troubleshooting

### Import Errors

If you see import errors, ensure `src/` is in Python path:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
```

### Mock Not Working

Ensure mocks are set up BEFORE importing the module:

```python
# Mock FIRST
sys.modules['RPi.GPIO'] = MagicMock()

# Then import
from thermostat import ThermostatController
```

### Environment Variables

Tests set environment variables in `setUp()`:

```python
def setUp(self):
    self.env_patcher = patch.dict(os.environ, {
        'TARGET_TEMP_HEAT': '68.0',
        ...
    })
    self.env_patcher.start()
```

## Coverage Goals

Target: **>80% code coverage** for src/ modules

Check coverage:
```bash
pytest tests/unit/ --cov=src --cov-report=term-missing
```

## Adding Tests for New Features

When adding new functionality:

1. Write tests FIRST (TDD approach)
2. Run tests to see them fail
3. Implement feature
4. Run tests to see them pass
5. Refactor if needed
6. Update this guide

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
