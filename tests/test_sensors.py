#!/usr/bin/env python3
"""
Test script for DS18B20 temperature sensors
"""

import sys
import time

try:
    from w1thermsensor import W1ThermSensor, Sensor
except ImportError:
    print("Error: w1thermsensor library not installed")
    print("Install with: pip install w1thermsensor")
    sys.exit(1)


def main():
    print("=" * 60)
    print("DS18B20 Temperature Sensor Test")
    print("=" * 60)
    print()
    
    # Get all available sensors
    try:
        sensors = W1ThermSensor.get_available_sensors()
    except Exception as e:
        print(f"Error: Unable to detect sensors: {e}")
        print()
        print("Troubleshooting steps:")
        print("1. Check if 1-Wire is enabled: lsmod | grep w1")
        print("2. Check for devices: ls /sys/bus/w1/devices/")
        print("3. Verify wiring: GPIO 4, 3.3V, GND with 4.7kΩ pull-up")
        return
    
    if not sensors:
        print("No sensors detected!")
        print()
        print("Troubleshooting:")
        print("- Check wiring connections")
        print("- Verify 4.7kΩ pull-up resistor between data line and 3.3V")
        print("- Try: ls /sys/bus/w1/devices/")
        return
    
    print(f"Found {len(sensors)} sensor(s):")
    print()
    
    # Display each sensor
    for i, sensor in enumerate(sensors, 1):
        print(f"Sensor #{i}")
        print(f"  ID: {sensor.id}")
        print(f"  Type: {sensor.type}")
        
        try:
            temp_c = sensor.get_temperature()
            temp_f = (temp_c * 9/5) + 32
            print(f"  Temperature: {temp_c:.2f}°C / {temp_f:.2f}°F")
        except Exception as e:
            print(f"  Error reading temperature: {e}")
        
        print()
    
    # Continuous reading
    print("=" * 60)
    print("Continuous Reading (Ctrl+C to stop)")
    print("=" * 60)
    print()
    
    try:
        while True:
            print(f"\n[{time.strftime('%H:%M:%S')}]")
            
            for sensor in sensors:
                try:
                    temp_c = sensor.get_temperature()
                    temp_f = (temp_c * 9/5) + 32
                    print(f"  {sensor.id}: {temp_f:.1f}°F ({temp_c:.1f}°C)")
                except Exception as e:
                    print(f"  {sensor.id}: ERROR - {e}")
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\nTest complete!")


if __name__ == '__main__':
    main()
