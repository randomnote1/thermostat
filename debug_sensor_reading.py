#!/home/pi/thermostat/venv/bin/python3
"""
Debug script to check what temperature sensors are actually returning
Run with: ./debug_sensor_reading.py
Or: ~/thermostat/venv/bin/python3 debug_sensor_reading.py
"""

try:
    from w1thermsensor import W1ThermSensor
    
    print("Reading DS18B20 sensors...")
    print("=" * 60)
    
    for sensor in W1ThermSensor.get_available_sensors():
        print(f"\nSensor ID: {sensor.id}")
        
        # Get temperature in Celsius (default)
        temp_c = sensor.get_temperature()
        
        # Manual conversion to Fahrenheit
        temp_f = (temp_c * 9/5) + 32
        
        # Manual conversion to Kelvin
        temp_k = temp_c + 273.15
        
        print(f"  Celsius:    {temp_c:.2f}°C")
        print(f"  Fahrenheit: {temp_f:.2f}°F")
        print(f"  Kelvin:     {temp_k:.2f}K")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("\nMake sure w1thermsensor is installed:")
    print("  pip3 install w1thermsensor")
except Exception as e:
    print(f"Error: {e}")
