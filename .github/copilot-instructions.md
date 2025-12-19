# GitHub Copilot Instructions for Raspberry Pi Thermostat Project

## Project Overview

This is a multi-zone thermostat system for Raspberry Pi 3B that controls HVAC systems while intelligently handling temperature anomalies from a nearby fireplace. The system operates completely offline and is designed for safety, reliability, and energy efficiency.

## Core Principles

### Safety First
- **HVAC Safety**: Never suggest code that could activate both heating and cooling simultaneously
- **Electrical Safety**: All HVAC control must go through optocoupler-isolated relays
- **Fail-Safe**: Always include proper error handling and graceful degradation
- **Emergency Limits**: Enforce temperature bounds (32°F - 100°F) to detect sensor failures

### Design Philosophy
- **Reliability Over Features**: Prefer simple, tested code over complex algorithms
- **Offline Operation**: No network dependencies, no cloud services
- **Low Power**: E-ink display, minimal CPU usage, efficient polling
- **Maintainability**: Clear code comments, logging for troubleshooting

## Architecture

### Hardware Components
- Raspberry Pi 3B (BCM GPIO numbering)
- DS18B20 1-Wire temperature sensors (multiple rooms)
- 4-channel relay board (5V, active HIGH)
- Waveshare 2.13" e-ink display HAT
- 24VAC to 5VDC isolated power supply

### Software Stack
- Python 3.9+ on Raspberry Pi OS Lite
- No GUI, runs as systemd service
- Libraries: RPi.GPIO, w1thermsensor, Pillow, python-dotenv

### Key Modules
- `src/thermostat.py` - Main control loop and HVAC logic
- `src/display.py` - E-ink display management
- `tests/test_*.py` - Hardware testing utilities

## Coding Standards

### Python Style
- Follow PEP 8 conventions
- Type hints for function signatures
- Docstrings for all classes and public methods
- Clear variable names (e.g., `system_temperature` not `sys_temp`)

### Error Handling
```python
# Always wrap hardware access in try-except
try:
    temperature = sensor.get_temperature()
except Exception as e:
    logger.error(f"Sensor read failed: {e}")
    # Implement graceful fallback
```

### Logging
- Use Python logging module, not print()
- Log levels: DEBUG (sensor reads), INFO (state changes), WARNING (anomalies), ERROR (failures)
- Include context in log messages: `logger.info(f"HVAC activated: {mode} at {temp}°F")`

### Configuration
- All settings in `config.env` loaded via python-dotenv
- Never hardcode temperatures, GPIO pins, or timing values
- Provide sensible defaults with `os.getenv('KEY', default_value)`

## Domain-Specific Guidelines

### Temperature Handling
- **Always use Fahrenheit** internally (user preference)
- DS18B20 returns Celsius, convert immediately: `temp_f = (temp_c * 9/5) + 32`
- Round display values: `f"{temp:.1f}°F"`
- Use median (not mean) for multi-sensor aggregation to resist outliers

### Anomaly Detection
The core feature that solves the fireplace problem:
```python
# Detect rapid temperature rise (fireplace ignition)
if temp_change > ANOMALY_THRESHOLD:  # e.g., 3°F in 5 minutes
    mark_sensor_compromised()

# Detect deviation from average (proximity to heat source)
if sensor_temp > avg_temp + DEVIATION_THRESHOLD:  # e.g., 5°F
    mark_sensor_compromised()
```

### HVAC Control Rules
```python
# Enforce minimum run time (prevent short-cycling)
if hvac_running and time_since_start < MIN_RUN_TIME:
    return  # Don't turn off yet

# Enforce minimum rest time (compressor protection)
if not hvac_running and time_since_stop < MIN_REST_TIME:
    return  # Don't turn on yet

# Use hysteresis to prevent oscillation
if temp < target - HYSTERESIS:
    activate_heat()
elif temp > target + HYSTERESIS:
    deactivate_heat()
```

### GPIO Best Practices
```python
# Always use BCM numbering
GPIO.setmode(GPIO.BCM)

# Set initial state explicitly
GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

# Clean up on exit
try:
    # main loop
finally:
    GPIO.cleanup()
```

### E-Ink Display
- Update sparingly (slow refresh, ~10-15 seconds)
- Use 1-bit color mode (black and white)
- Put display to sleep when not updating (power saving)
- Handle missing display gracefully (system works without it)

## Testing Requirements

### Hardware Testing
- Always provide test scripts for new hardware features
- Test scripts should be interactive and informative
- Include troubleshooting hints in test output

### Integration Testing
- Test HVAC logic WITHOUT actual HVAC connection first
- Simulate sensor readings for edge cases
- Verify safety interlocks (heat+cool never both on)

### Mock Mode
When RPi.GPIO or w1thermsensor unavailable:
```python
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    # Use mock implementations for development
```

## Common Patterns

### Sensor Reading Loop
```python
def read_sensors(self) -> List[SensorReading]:
    readings = []
    try:
        for sensor in W1ThermSensor.get_available_sensors():
            temp_c = sensor.get_temperature()
            temp_f = (temp_c * 9/5) + 32
            readings.append(SensorReading(sensor.id, name, temp_f, datetime.now()))
    except Exception as e:
        logger.error(f"Sensor read error: {e}")
    return readings
```

### State Management
```python
# Track state changes for time-based logic
if new_state != self.current_state:
    self.current_state = new_state
    self.state_change_time = datetime.now()
    logger.info(f"State changed to: {new_state}")
```

### Time-Based Checks
```python
# Use timedelta for readable time comparisons
elapsed = (datetime.now() - self.last_update).total_seconds()
if elapsed >= self.update_interval:
    self.update()
```

## What NOT to Suggest

❌ Network connectivity (WiFi, Ethernet, APIs)
❌ Cloud services or external dependencies
❌ GUI frameworks (this is headless)
❌ Complex ML/AI (keep it simple and deterministic)
❌ Database systems (config file + logs are sufficient)
❌ Non-isolated relay control (safety violation)
❌ Direct GPIO control without proper setup/cleanup
❌ Hard-coded sensor IDs or GPIO pins

## What TO Suggest

✅ Additional safety checks and interlocks
✅ Better error handling and recovery
✅ Improved logging and diagnostics
✅ More robust sensor failure detection
✅ Enhanced anomaly detection algorithms
✅ Performance optimizations (but maintain readability)
✅ Better documentation and comments
✅ Additional test coverage

## File-Specific Guidelines

### src/thermostat.py
- Keep control loop simple and readable
- Add comments explaining HVAC timing decisions
- Log state changes for troubleshooting
- Handle missing sensors gracefully

### tests/test_*.py
- Make interactive and user-friendly
- Provide clear troubleshooting steps
- Safe for repeated runs (no persistent state changes)

### config/config.env
- Document units in comments (°F, seconds, etc.)
- Provide sensible defaults
- Group related settings together

## Hardware Constraints

- **DS18B20**: 750ms conversion time, don't poll too fast
- **E-Ink**: Slow refresh (10-15s), limited to ~1 update/minute
- **Relays**: Mechanical, have minimum switching time
- **GPIO**: 3.3V logic, max 16mA per pin
- **Pi 3B**: Quad-core ARM, plenty of power for this application

## Debugging Tips

When suggesting debugging code:
```python
# Helpful debug logging
logger.debug(f"Sensor {id}: {temp:.2f}°F, "
            f"compromised={is_compromised}, "
            f"history_len={len(history)}")

# State dumps for troubleshooting
logger.info(f"System state: {self.get_status()}")
```

## Example Code Patterns

### Adding a New Sensor Type
```python
class BME280Reader:
    """Handle BME280 humidity sensors"""
    def __init__(self, i2c_address):
        self.address = i2c_address
        # Initialize sensor
    
    def read(self) -> Tuple[float, float]:
        """Returns (temperature_f, humidity_percent)"""
        # Implementation
        pass
```

### Adding a New HVAC Mode
```python
def control_hvac_auto(self, system_temp: float) -> None:
    """Auto mode: heat or cool to maintain comfort"""
    if system_temp < self.target_temp_heat - self.hysteresis:
        self._set_hvac_state(heat=True, cool=False)
    elif system_temp > self.target_temp_cool + self.hysteresis:
        self._set_hvac_state(heat=False, cool=True)
    else:
        self._set_hvac_state(heat=False, cool=False)
```

## Documentation Standards

When suggesting new features:
1. Update README.md with usage instructions
2. Add configuration options to config/config.example.env
3. Create test script in tests/ if hardware-related
4. Update docs/INSTALL.md if installation steps change
5. Add wiring diagrams for new hardware

## Performance Considerations

- Sensor reads: Every 30 seconds (don't overwhelm 1-Wire bus)
- HVAC decisions: Every 60 seconds (thermal systems are slow)
- Display updates: Every 60 seconds (e-ink is slow)
- Log rotation: Prevent logs from filling SD card

## Security Considerations

- No web interface = no network attack surface
- No remote access = no unauthorized control
- Physical access required for configuration changes
- Consider: Add PIN code protection if adding user input

## Future Enhancement Ideas

When user asks for features, consider:
- Web dashboard (read-only, local network)
- Data logging to CSV for analysis
- Scheduling (time-based temperature setpoints)
- Humidity control integration
- Multi-stage HVAC support (already partly implemented)
- Weather-based preconditioning
- Vacation mode

Always maintain backward compatibility and safety as top priorities.
