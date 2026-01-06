#!/usr/bin/env python3
"""
Debug script to check what temperature sensors are actually returning
"""

try:
    from w1thermsensor import W1ThermSensor
    
    print("Reading DS18B20 sensors...")
    print("=" * 60)
    
    for sensor in W1ThermSensor.get_available_sensors():
        print(f"\nSensor ID: {sensor.id}")
        
        # Get temperature in different units
        temp_c = sensor.get_temperature()
        temp_f = sensor.get_temperature(W1ThermSensor.DEGREES_F)
        temp_k = sensor.get_temperature(W1ThermSensor.KELVIN)
        
        print(f"  Celsius:    {temp_c:.2f}°C")
        print(f"  Fahrenheit: {temp_f:.2f}°F")
        print(f"  Kelvin:     {temp_k:.2f}K")
        
        # Manual conversion to check
        manual_f = (temp_c * 9/5) + 32
        print(f"  Manual C→F: {manual_f:.2f}°F")
        print(f"  Difference: {abs(temp_f - manual_f):.4f}°F")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("\nMake sure w1thermsensor is installed:")
    print("  pip3 install w1thermsensor")
except Exception as e:
    print(f"Error: {e}")
