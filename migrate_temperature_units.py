#!/usr/bin/env python3
"""
One-time migration script to convert existing database temperatures from Fahrenheit to Celsius.

Run this script once after updating to the temperature units feature.
It will detect if temperatures are in Fahrenheit and convert them to Celsius.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import ThermostatDatabase
from temperature_utils import fahrenheit_to_celsius


def migrate_database(db_path='thermostat.db'):
    """Migrate database temperatures from Fahrenheit to Celsius if needed"""
    
    db = ThermostatDatabase(db_path)
    
    # First, ensure the temperature_units column exists in the schema
    print("Checking database schema...")
    
    with db._get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if temperature_units column exists
        cursor.execute("PRAGMA table_info(settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'temperature_units' not in columns:
            print("  Adding temperature_units column to settings table...")
            cursor.execute("ALTER TABLE settings ADD COLUMN temperature_units TEXT DEFAULT 'F'")
            conn.commit()
            print("  ✓ Schema updated")
        else:
            print("  ✓ Schema already up to date")
    
    # Load current settings
    settings = db.load_settings()
    
    if not settings:
        print("No settings found in database. Nothing to migrate.")
        return
    
    heat = settings['target_temp_heat']
    cool = settings['target_temp_cool']
    
    print(f"Current database values:")
    print(f"  Heat: {heat}")
    print(f"  Cool: {cool}")
    
    # Heuristic: If either temperature is > 40, it's likely in Fahrenheit
    # (40°C = 104°F, way too hot for a thermostat setpoint)
    if heat > 40 or cool > 40:
        print("\n⚠️  Values appear to be in Fahrenheit. Converting to Celsius...")
        
        # Convert from Fahrenheit to Celsius
        heat_celsius = fahrenheit_to_celsius(heat)
        cool_celsius = fahrenheit_to_celsius(cool)
        
        print(f"  Heat: {heat}°F → {heat_celsius:.1f}°C")
        print(f"  Cool: {cool}°F → {cool_celsius:.1f}°C")
        
        # Save converted values
        db.save_settings(
            target_temp_heat=heat_celsius,
            target_temp_cool=cool_celsius,
            hvac_mode=settings['hvac_mode'],
            fan_mode=settings.get('fan_mode', 'auto'),
            temperature_units=settings.get('temperature_units', 'F')
        )
        
        # Log the change
        db.log_setting_change('target_temp_heat', str(heat), str(heat_celsius), 'migration_script')
        db.log_setting_change('target_temp_cool', str(cool), str(cool_celsius), 'migration_script')
        
        print("\n✅ Migration complete! Temperatures converted to Celsius.")
        print("   The display will still show Fahrenheit based on your temperature_units setting.")
        
    else:
        print("\n✅ Values appear to already be in Celsius. No migration needed.")
    
    # Also check schedules
    schedules = db.get_schedules()
    migrated_schedules = 0
    
    for schedule in schedules:
        schedule_id = schedule['id']
        heat_temp = schedule.get('target_temp_heat')
        cool_temp = schedule.get('target_temp_cool')
        
        needs_migration = False
        
        if heat_temp and heat_temp > 40:
            heat_temp = fahrenheit_to_celsius(heat_temp)
            needs_migration = True
        
        if cool_temp and cool_temp > 40:
            cool_temp = fahrenheit_to_celsius(cool_temp)
            needs_migration = True
        
        if needs_migration:
            db.update_schedule(
                schedule_id,
                target_temp_heat=heat_temp,
                target_temp_cool=cool_temp
            )
            migrated_schedules += 1
            print(f"  Migrated schedule: {schedule['name']}")
    
    if migrated_schedules > 0:
        print(f"\n✅ Migrated {migrated_schedules} schedule(s)")
    
    # Migrate sensor history
    print("\nMigrating sensor history...")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        
        # Get sample of recent sensor readings to check if migration needed
        cursor.execute("SELECT temperature FROM sensor_history LIMIT 100")
        temps = [row[0] for row in cursor.fetchall()]
        
        if temps:
            avg_temp = sum(temps) / len(temps)
            
            # If average temperature is > 40, assume Fahrenheit
            if avg_temp > 40:
                print(f"  Sensor history appears to be in Fahrenheit (avg: {avg_temp:.1f})")
                print("  Converting all sensor readings to Celsius...")
                
                # Convert all sensor readings
                cursor.execute("""
                    UPDATE sensor_history 
                    SET temperature = (temperature - 32.0) * 5.0 / 9.0
                """)
                
                rows_updated = cursor.rowcount
                conn.commit()
                print(f"  ✅ Converted {rows_updated} sensor readings")
            else:
                print(f"  ✅ Sensor history already in Celsius (avg: {avg_temp:.1f}°C)")
        else:
            print("  No sensor history found")
    
    # Migrate HVAC history
    print("\nMigrating HVAC history...")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        
        # Get sample of recent HVAC readings to check if migration needed
        cursor.execute("SELECT system_temp FROM hvac_history WHERE system_temp IS NOT NULL LIMIT 100")
        temps = [row[0] for row in cursor.fetchall()]
        
        if temps:
            avg_temp = sum(temps) / len(temps)
            
            # If average temperature is > 40, assume Fahrenheit
            if avg_temp > 40:
                print(f"  HVAC history appears to be in Fahrenheit (avg: {avg_temp:.1f})")
                print("  Converting all HVAC system_temp and target_temp readings...")
                
                # Convert system_temp and target_temp
                cursor.execute("""
                    UPDATE hvac_history 
                    SET system_temp = (system_temp - 32.0) * 5.0 / 9.0,
                        target_temp = (target_temp - 32.0) * 5.0 / 9.0
                    WHERE system_temp IS NOT NULL
                """)
                
                rows_updated = cursor.rowcount
                conn.commit()
                print(f"  ✅ Converted {rows_updated} HVAC history records")
            else:
                print(f"  ✅ HVAC history already in Celsius (avg: {avg_temp:.1f}°C)")
        else:
            print("  No HVAC history found")


if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'thermostat.db'
    
    print("=" * 60)
    print("Temperature Units Migration Script")
    print("=" * 60)
    print(f"Database: {db_path}\n")
    
    migrate_database(db_path)
    
    print("\n" + "=" * 60)
    print("Migration complete. Please restart your thermostat.")
    print("=" * 60)
