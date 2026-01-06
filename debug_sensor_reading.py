#!/home/pi/thermostat/venv/bin/python3
"""
Debug script to check DS18B20 sensor readings

⚠️  COMMON ISSUE: Readings 8-10°F too high?
    
    The Raspberry Pi uses 3.3V logic, but most DS18B20 tutorials
    show 4.7kΩ pull-up resistors (designed for 5V Arduino).
    
    **SOLUTION: Replace 4.7kΩ resistor with 2.7kΩ resistor**
    
    This is a known issue with 1-Wire devices on 3.3V systems.
    Reference: https://github.com/PaulStoffregen/OneWire/issues/91
    
    Your hardware likely has a 4.7kΩ resistor between DATA and VDD.
    Simply replace it with a 2.7kΩ resistor for accurate readings.

Usage:
    ./debug_sensor_reading.py
    or: ~/thermostat/venv/bin/python3 debug_sensor_reading.py
"""

try:
    from w1thermsensor import W1ThermSensor
    
    print("=" * 60)
    print("DS18B20 Temperature Sensor Debug")
    print("=" * 60)
    print()
    
    sensors = list(W1ThermSensor.get_available_sensors())
    
    if not sensors:
        print("⚠️  No sensors detected!")
        print("\nTroubleshooting:")
        print("  1. Check 1-Wire is enabled: ls /sys/bus/w1/devices/")
        print("  2. Check wiring: DATA→GPIO4, VDD→3.3V, GND→GND")
        print("  3. Check pull-up resistor present (2.7kΩ or 4.7kΩ)")
        exit(1)
    
    print(f"Found {len(sensors)} sensor(s)\n")
    
    for sensor in sensors:
        print(f"Sensor ID: {sensor.id}")
        
        # Get temperature in Celsius (what DS18B20 actually returns)
        temp_c = sensor.get_temperature()
        
        # Manual conversion to Fahrenheit
        temp_f = (temp_c * 9/5) + 32
        
        # Manual conversion to Kelvin
        temp_k = temp_c + 273.15
        
        print(f"  Celsius:    {temp_c:.2f}°C")
        print(f"  Fahrenheit: {temp_f:.2f}°F")
        print(f"  Kelvin:     {temp_k:.2f}K")
        print()
    
    # Diagnostic check
    avg_f = sum((s.get_temperature() * 9/5 + 32) for s in sensors) / len(sensors)
    
    print("=" * 60)
    if 60 <= avg_f <= 85:
        print("✅ Readings look normal for indoor temperature")
    elif avg_f > 85:
        print("⚠️  READINGS APPEAR TOO HIGH")
        print()
        print("This is likely caused by using a 4.7kΩ pull-up resistor")
        print("on a 3.3V system (Raspberry Pi).")
        print()
        print("HARDWARE FIX:")
        print("  1. Power off the Raspberry Pi")
        print("  2. Locate the resistor between DATA and VDD (3.3V)")
        print("  3. Replace the 4.7kΩ resistor with a 2.7kΩ resistor")
        print("  4. Power on and test again")
        print()
        print("The 2.7kΩ resistor provides proper pull-up voltage for")
        print("3.3V logic levels, fixing the ~10°F offset.")
    elif avg_f < 60:
        print("⚠️  Readings appear too low (check for draft/cold source)")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print()
    print("Make sure you're running with the venv Python:")
    print("  ~/thermostat/venv/bin/python3 debug_sensor_reading.py")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
