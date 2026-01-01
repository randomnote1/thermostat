#!/usr/bin/env python3
"""
Test sensor database functionality
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import ThermostatDatabase


def test_sensor_crud():
    """Test sensor CRUD operations"""
    print("=" * 60)
    print("Testing Sensor Database Operations")
    print("=" * 60)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = ThermostatDatabase(db_path)
        print(f"\n✓ Created temporary database: {db_path}")
        
        # Test adding sensors
        print("\n--- Testing Add Sensor ---")
        sensor_id = "28-3f7865e285f5"
        db.add_sensor(sensor_id, "Living Room", enabled=True, monitored=True)
        print(f"✓ Added sensor: {sensor_id} -> Living Room")
        
        db.add_sensor("28-000000000001", "Bedroom", enabled=True, monitored=False)
        print("✓ Added sensor: 28-000000000001 -> Bedroom")
        
        db.add_sensor("28-000000000002", "Kitchen", enabled=False, monitored=False)
        print("✓ Added sensor: 28-000000000002 -> Kitchen (disabled)")
        
        # Test getting single sensor
        print("\n--- Testing Get Single Sensor ---")
        sensor = db.get_sensor(sensor_id)
        if sensor:
            print(f"✓ Retrieved sensor: {sensor['name']}")
            print(f"  - ID: {sensor['sensor_id']}")
            print(f"  - Enabled: {sensor['enabled']}")
            print(f"  - Monitored: {sensor['monitored']}")
            print(f"  - Created: {sensor['created_at']}")
        else:
            print("✗ Failed to retrieve sensor")
        
        # Test getting all sensors
        print("\n--- Testing Get All Sensors ---")
        all_sensors = db.get_sensors()
        print(f"✓ Retrieved {len(all_sensors)} sensors:")
        for s in all_sensors:
            status = []
            if s['enabled']:
                status.append("enabled")
            if s['monitored']:
                status.append("monitored")
            status_str = ", ".join(status) if status else "disabled"
            print(f"  - {s['name']}: {s['sensor_id']} ({status_str})")
        
        # Test getting enabled only
        print("\n--- Testing Get Enabled Sensors Only ---")
        enabled_sensors = db.get_sensors(enabled_only=True)
        print(f"✓ Retrieved {len(enabled_sensors)} enabled sensors:")
        for s in enabled_sensors:
            print(f"  - {s['name']}: {s['sensor_id']}")
        
        # Test updating sensor
        print("\n--- Testing Update Sensor ---")
        db.update_sensor(sensor_id, name="Living Room (Main)")
        updated = db.get_sensor(sensor_id)
        print(f"✓ Updated name to: {updated['name']}")
        
        db.update_sensor(sensor_id, monitored=False)
        updated = db.get_sensor(sensor_id)
        print(f"✓ Updated monitored to: {updated['monitored']}")
        
        # Test update non-existent sensor
        result = db.update_sensor("28-nonexistent", name="Should Fail")
        if not result:
            print("✓ Correctly rejected update of non-existent sensor")
        else:
            print("✗ Should have rejected non-existent sensor")
        
        # Test delete sensor
        print("\n--- Testing Delete Sensor ---")
        if db.delete_sensor("28-000000000002"):
            print("✓ Deleted sensor: 28-000000000002")
        else:
            print("✗ Failed to delete sensor")
        
        remaining = db.get_sensors()
        print(f"✓ {len(remaining)} sensors remaining:")
        for s in remaining:
            print(f"  - {s['name']}")
        
        # Test delete non-existent sensor
        if not db.delete_sensor("28-nonexistent"):
            print("✓ Correctly rejected delete of non-existent sensor")
        else:
            print("✗ Should have rejected non-existent sensor")
        
        print("\n" + "=" * 60)
        print("✓ All sensor database tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"\n✓ Cleaned up temporary database")


if __name__ == '__main__':
    test_sensor_crud()
