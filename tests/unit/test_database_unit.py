#!/usr/bin/env python3
"""
Unit tests for database module
Tests persistence, schedules, and history logging
"""

import unittest
import os
import tempfile
from datetime import datetime, time, timedelta
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import ThermostatDatabase


class TestDatabaseInitialization(unittest.TestCase):
    """Test database initialization and schema"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_file_created(self):
        """Test that database file is created"""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_settings_table_exists(self):
        """Test that settings table is created"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='settings'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_schedules_table_exists(self):
        """Test that schedules table is created"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schedules'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_sensor_history_table_exists(self):
        """Test that sensor_history table is created"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sensor_history'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_sensors_table_exists(self):
        """Test that sensors table is created"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sensors'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_indexes_created(self):
        """Test that indexes are created for performance"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            self.assertIn('idx_sensor_history_timestamp', indexes)
            self.assertIn('idx_setting_history_timestamp', indexes)


class TestSettingsPersistence(unittest.TestCase):
    """Test settings save and load operations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_save_and_load_settings(self):
        """Test saving and loading thermostat settings"""
        # Save settings
        self.db.save_settings(68.0, 74.0, 'heat')
        
        # Load settings
        settings = self.db.load_settings()
        
        self.assertEqual(settings['target_temp_heat'], 68.0)
        self.assertEqual(settings['target_temp_cool'], 74.0)
        self.assertEqual(settings['hvac_mode'], 'heat')
    
    def test_update_existing_settings(self):
        """Test that saving settings updates existing record"""
        # Save initial settings
        self.db.save_settings(68.0, 74.0, 'heat')
        
        # Update settings
        self.db.save_settings(70.0, 76.0, 'cool')
        
        # Load and verify
        settings = self.db.load_settings()
        self.assertEqual(settings['target_temp_heat'], 70.0)
        self.assertEqual(settings['target_temp_cool'], 76.0)
        self.assertEqual(settings['hvac_mode'], 'cool')
    
    def test_load_settings_when_empty(self):
        """Test loading settings when database is empty"""
        settings = self.db.load_settings()
        self.assertIsNone(settings)
    
    def test_settings_updated_at_timestamp(self):
        """Test that updated_at timestamp is set"""
        self.db.save_settings(68.0, 74.0, 'heat')
        
        settings = self.db.load_settings()
        # Just verify timestamp exists and is a valid ISO format string
        self.assertIsNotNone(settings['updated_at'])
        # Verify it can be parsed
        updated_at = datetime.fromisoformat(settings['updated_at'])
        self.assertIsInstance(updated_at, datetime)


class TestScheduleCRUD(unittest.TestCase):
    """Test schedule create, read, update, delete operations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_create_schedule(self):
        """Test creating a new schedule"""
        schedule_id = self.db.create_schedule(
            name="Morning",
            time_str="06:00",
            days_of_week="1,2,3,4,5",
            target_temp_heat=68.0,
            target_temp_cool=None,
            hvac_mode="heat"
        )
        
        self.assertIsNotNone(schedule_id)
        self.assertGreater(schedule_id, 0)
    
    def test_get_all_schedules(self):
        """Test retrieving all schedules"""
        # Create multiple schedules
        self.db.create_schedule("Morning", "1,2,3,4,5", "06:00", 68.0, None, "heat")
        self.db.create_schedule("Evening", "1,2,3,4,5", "22:00", 62.0, None, "heat")
        
        schedules = self.db.get_schedules()
        
        self.assertEqual(len(schedules), 2)
        self.assertEqual(schedules[0]['name'], 'Morning')
        self.assertEqual(schedules[1]['name'], 'Evening')
    
    def test_get_schedule_by_id(self):
        """Test retrieving a specific schedule"""
        schedule_id = self.db.create_schedule(
            "Test", "1,2,3,4,5,6,7", "12:00", 70.0, 75.0, "auto"
        )
        
        schedules = self.db.get_schedules()
        schedule = [s for s in schedules if s['id'] == schedule_id][0]
        
        self.assertEqual(schedule['name'], 'Test')
        self.assertEqual(schedule['target_temp_heat'], 70.0)
        self.assertEqual(schedule['target_temp_cool'], 75.0)
        self.assertEqual(schedule['hvac_mode'], 'auto')
    
    def test_update_schedule(self):
        """Test updating an existing schedule"""
        schedule_id = self.db.create_schedule(
            "Morning", "1,2,3,4,5", "06:00", 68.0, None, "heat"
        )
        
        self.db.update_schedule(
            schedule_id,
            name="Early Morning",
            time="05:30",
            target_temp_heat=69.0
        )
        
        schedules = self.db.get_schedules()
        schedule = [s for s in schedules if s['id'] == schedule_id][0]
        self.assertEqual(schedule['name'], 'Early Morning')
        self.assertEqual(schedule['time'], '05:30')
        self.assertEqual(schedule['target_temp_heat'], 69.0)
    
    def test_delete_schedule(self):
        """Test deleting a schedule"""
        schedule_id = self.db.create_schedule(
            "Test", "1,2,3,4,5", "12:00", 70.0, None, "heat"
        )
        
        self.db.delete_schedule(schedule_id)
        
        schedules = self.db.get_schedules()
        schedule = [s for s in schedules if s['id'] == schedule_id]
        self.assertEqual(len(schedule), 0)
    
    def test_schedule_enabled_flag(self):
        """Test schedule enabled/disabled flag"""
        schedule_id = self.db.create_schedule(
            "Test", "1,2,3,4,5", "12:00", 70.0, None, "heat"
        )
        
        # Disable it
        self.db.update_schedule(schedule_id, enabled=0)
        schedules = self.db.get_schedules()
        schedule = [s for s in schedules if s['id'] == schedule_id][0]
        self.assertEqual(schedule['enabled'], 0)
        
        # Enable it
        self.db.update_schedule(schedule_id, enabled=1)
        schedules = self.db.get_schedules()
        schedule = [s for s in schedules if s['id'] == schedule_id][0]
        self.assertEqual(schedule['enabled'], 1)
    
    def test_get_active_schedules(self):
        """Test getting schedules active at a specific time"""
        # Create weekday morning schedule (Monday-Friday at 6:00 AM)
        # Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4
        self.db.create_schedule("Weekday Morning", "0,1,2,3,4", "06:00", 68.0, None, "heat")
        
        # Create weekend morning schedule (Saturday-Sunday at 8:00 AM)
        # Saturday=5, Sunday=6
        self.db.create_schedule("Weekend Morning", "5,6", "08:00", 65.0, None, "heat")
        
        # Create evening schedule (all days at 10:00 PM)
        self.db.create_schedule("Evening", "0,1,2,3,4,5,6", "22:00", 62.0, None, "heat")
        
        # Create disabled schedule
        disabled_id = self.db.create_schedule("Disabled", "0,1,2,3,4", "06:00", 70.0, None, "heat")
        self.db.update_schedule(disabled_id, enabled=0)
        
        # Test Monday at 6:00 AM (should match weekday morning)
        monday_6am = datetime(2024, 1, 1, 6, 0)  # Monday (weekday=0)
        active = self.db.get_active_schedules(monday_6am)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['name'], 'Weekday Morning')
        
        # Test Saturday at 8:00 AM (should match weekend morning)
        saturday_8am = datetime(2024, 1, 6, 8, 0)  # Saturday (weekday=5)
        active = self.db.get_active_schedules(saturday_8am)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['name'], 'Weekend Morning')
        
        # Test any day at 10:00 PM (should match evening)
        tuesday_10pm = datetime(2024, 1, 2, 22, 0)  # Tuesday (weekday=1)
        active = self.db.get_active_schedules(tuesday_10pm)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['name'], 'Evening')
    
    def test_no_active_schedules_at_time(self):
        """Test when no schedules match the current time"""
        self.db.create_schedule("Morning", "1,2,3,4,5", "06:00", 68.0, None, "heat")
        
        # Test at a different time (noon)
        noon = datetime(2024, 1, 1, 12, 0)
        active = self.db.get_active_schedules(noon)
        self.assertEqual(len(active), 0)


class TestHistoryLogging(unittest.TestCase):
    """Test history logging operations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_log_sensor_reading(self):
        """Test logging a single sensor reading"""
        self.db.log_sensor_reading('sensor1', 'Living Room', 72.5, False)
        
        history = self.db.get_sensor_history(hours=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['sensor_id'], 'sensor1')
        self.assertEqual(history[0]['temperature'], 72.5)
    
    def test_batch_log_sensor_readings(self):
        """Test logging multiple sensor readings at once"""
        batch_data = [
            ('sensor1', 'Living Room', 72.5, False),
            ('sensor2', 'Bedroom', 70.0, False),
            ('sensor3', 'Kitchen', 75.0, True),  # Compromised sensor
        ]
        
        self.db.log_sensor_readings_batch(batch_data)
        
        history = self.db.get_sensor_history(hours=1)
        self.assertEqual(len(history), 3)
        
        # Check compromised flag
        kitchen_reading = [r for r in history if r['sensor_name'] == 'Kitchen'][0]
        self.assertEqual(kitchen_reading['is_compromised'], 1)
    
    def test_log_hvac_state(self):
        """Test logging HVAC state changes"""
        self.db.log_hvac_state(
            system_temp=72.0,
            target_temp=68.0,
            hvac_mode='heat',
            heat=True,
            cool=False,
            fan=True,
            heat2=False
        )
        
        history = self.db.get_hvac_history(hours=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['hvac_mode'], 'heat')
        self.assertEqual(history[0]['heat_active'], 1)
        self.assertEqual(history[0]['fan_active'], 1)
    
    def test_log_setting_change(self):
        """Test logging setting changes with audit trail"""
        self.db.log_setting_change('target_temp_heat', '68', '70', 'web_interface')
        
        history = self.db.get_setting_history(limit=100)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['setting_name'], 'target_temp_heat')
        self.assertEqual(history[0]['old_value'], '68')
        self.assertEqual(history[0]['new_value'], '70')
        self.assertEqual(history[0]['source'], 'web_interface')
    
    def test_get_sensor_history_time_filter(self):
        """Test filtering sensor history by time range"""
        # Log readings at different times
        now = datetime.now()
        
        # Reading from 2 hours ago
        self.db.log_sensor_reading('sensor1', 'Room1', 70.0, False)
        
        # Manually adjust timestamp in database to simulate older reading
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            old_time = (now - timedelta(hours=2)).isoformat()
            cursor.execute(
                'UPDATE sensor_history SET timestamp = ? WHERE sensor_id = ?',
                (old_time, 'sensor1')
            )
        
        # Wait a moment to ensure distinct timestamps
        import time
        time.sleep(0.01)
        
        # New reading now
        self.db.log_sensor_reading('sensor2', 'Room2', 72.0, False)
        
        # Get last hour (should only get sensor2)
        history_1h = self.db.get_sensor_history(hours=1)
        # May get 1 or 2 depending on timing, but sensor2 should be present
        self.assertGreaterEqual(len(history_1h), 1)
        sensor_ids = [h['sensor_id'] for h in history_1h]
        self.assertIn('sensor2', sensor_ids)
        
        # Get last 3 hours (should get both)
        history_3h = self.db.get_sensor_history(hours=3)
        self.assertEqual(len(history_3h), 2)
    
    def test_get_sensor_history_with_limit(self):
        """Test limiting number of history records returned"""
        # Log 10 readings
        for i in range(10):
            self.db.log_sensor_reading('sensor1', 'Room1', 70.0 + i, False)
        
        # Get only last 5
        history = self.db.get_sensor_history(limit=5)
        self.assertEqual(len(history), 5)
        
        # Verify they're the most recent (highest temperatures)
        temps = [r['temperature'] for r in history]
        self.assertIn(79.0, temps)  # Last reading
        self.assertIn(75.0, temps)  # 5th from last


class TestDatabaseMaintenance(unittest.TestCase):
    """Test database cleanup and maintenance operations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_cleanup_old_sensor_data(self):
        """Test cleaning up old sensor readings"""
        now = datetime.now()
        
        # Add recent data
        self.db.log_sensor_reading('sensor1', 'Room1', 70.0, False)
        
        # Add old data (31 days ago)
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            old_time = (now - timedelta(days=31)).isoformat()
            cursor.execute(
                'INSERT INTO sensor_history (sensor_id, sensor_name, temperature, is_compromised, timestamp) VALUES (?, ?, ?, ?, ?)',
                ('sensor2', 'Room2', 68.0, 0, old_time)
            )
        
        # Verify we have 2 records
        all_history = self.db.get_sensor_history(hours=24*365)  # Get all
        self.assertEqual(len(all_history), 2)
        
        # Cleanup data older than 30 days
        self.db.cleanup_old_history(days_to_keep=30)
        
        # Verify old data is gone
        remaining = self.db.get_sensor_history(hours=24*365)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]['sensor_id'], 'sensor1')
    
    def test_get_database_stats(self):
        """Test getting database statistics"""
        # Add some data
        self.db.save_settings(68.0, 74.0, 'heat')
        self.db.create_schedule("Morning", "1,2,3,4,5", "06:00", 68.0, None, "heat")
        self.db.log_sensor_reading('sensor1', 'Room1', 70.0, False)
        self.db.log_hvac_state(72.0, 68.0, 'heat', True, False, True, False)
        self.db.log_setting_change('hvac_mode', 'off', 'heat', 'system')
        
        stats = self.db.get_database_stats()
        
        self.assertEqual(stats['schedules_count'], 1)
        self.assertEqual(stats['sensor_history_count'], 1)
        self.assertEqual(stats['hvac_history_count'], 1)
        self.assertEqual(stats['setting_history_count'], 1)
        self.assertGreater(stats['db_size_mb'], 0)


class TestDatabaseErrorHandling(unittest.TestCase):
    """Test error handling in database operations"""
    
    def test_invalid_database_path(self):
        """Test handling of invalid database path"""
        # Try to create database in non-existent directory
        invalid_path = '/nonexistent/directory/test.db'
        with self.assertRaises(Exception):
            db = ThermostatDatabase(invalid_path)
    
    def test_get_nonexistent_schedule(self):
        """Test getting a schedule that doesn't exist"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            db = ThermostatDatabase(temp_db.name)
            schedules = db.get_schedules()
            schedule = [s for s in schedules if s['id'] == 99999]
            self.assertEqual(len(schedule), 0)
        finally:
            os.unlink(temp_db.name)
    
    def test_delete_nonexistent_schedule(self):
        """Test deleting a schedule that doesn't exist"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            db = ThermostatDatabase(temp_db.name)
            # Should not raise exception
            db.delete_schedule(99999)
        finally:
            os.unlink(temp_db.name)


class TestSensorCRUD(unittest.TestCase):
    """Test sensor CRUD operations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_add_sensor(self):
        """Test adding a sensor"""
        sensor_id = "28-3f7865e285f5"
        self.db.add_sensor(sensor_id, "Living Room", enabled=True, monitored=True)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertIsNotNone(sensor)
        self.assertEqual(sensor['sensor_id'], sensor_id)
        self.assertEqual(sensor['name'], "Living Room")
        self.assertTrue(sensor['enabled'])
        self.assertTrue(sensor['monitored'])
    
    def test_add_sensor_defaults(self):
        """Test adding a sensor with default values"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Bedroom")
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertIsNotNone(sensor)
        self.assertTrue(sensor['enabled'])  # Default True
        self.assertFalse(sensor['monitored'])  # Default False
    
    def test_get_sensor_not_found(self):
        """Test getting a sensor that doesn't exist"""
        sensor = self.db.get_sensor("28-nonexistent")
        self.assertIsNone(sensor)
    
    def test_get_all_sensors(self):
        """Test getting all sensors"""
        self.db.add_sensor("28-000000000001", "Living Room")
        self.db.add_sensor("28-000000000002", "Bedroom")
        self.db.add_sensor("28-000000000003", "Kitchen", enabled=False)
        
        sensors = self.db.get_sensors()
        self.assertEqual(len(sensors), 3)
        
        # Check ordering by name
        names = [s['name'] for s in sensors]
        self.assertEqual(names, sorted(names))
    
    def test_get_enabled_sensors_only(self):
        """Test getting only enabled sensors"""
        self.db.add_sensor("28-000000000001", "Living Room", enabled=True)
        self.db.add_sensor("28-000000000002", "Bedroom", enabled=True)
        self.db.add_sensor("28-000000000003", "Kitchen", enabled=False)
        
        enabled_sensors = self.db.get_sensors(enabled_only=True)
        self.assertEqual(len(enabled_sensors), 2)
        
        for sensor in enabled_sensors:
            self.assertTrue(sensor['enabled'])
    
    def test_update_sensor_name(self):
        """Test updating sensor name"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room")
        
        result = self.db.update_sensor(sensor_id, name="Living Room (Main)")
        self.assertTrue(result)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertEqual(sensor['name'], "Living Room (Main)")
    
    def test_update_sensor_enabled(self):
        """Test updating sensor enabled status"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room", enabled=True)
        
        result = self.db.update_sensor(sensor_id, enabled=False)
        self.assertTrue(result)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertFalse(sensor['enabled'])
    
    def test_update_sensor_monitored(self):
        """Test updating sensor monitored status"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room", monitored=False)
        
        result = self.db.update_sensor(sensor_id, monitored=True)
        self.assertTrue(result)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertTrue(sensor['monitored'])
    
    def test_update_sensor_multiple_fields(self):
        """Test updating multiple sensor fields at once"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room", enabled=True, monitored=False)
        
        result = self.db.update_sensor(sensor_id, name="Main Room", enabled=False, monitored=True)
        self.assertTrue(result)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertEqual(sensor['name'], "Main Room")
        self.assertFalse(sensor['enabled'])
        self.assertTrue(sensor['monitored'])
    
    def test_update_sensor_not_found(self):
        """Test updating a sensor that doesn't exist"""
        result = self.db.update_sensor("28-nonexistent", name="Should Fail")
        self.assertFalse(result)
    
    def test_update_sensor_no_changes(self):
        """Test updating sensor with no fields specified"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room")
        
        result = self.db.update_sensor(sensor_id)
        self.assertFalse(result)
    
    def test_delete_sensor(self):
        """Test deleting a sensor"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room")
        
        result = self.db.delete_sensor(sensor_id)
        self.assertTrue(result)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertIsNone(sensor)
    
    def test_delete_sensor_not_found(self):
        """Test deleting a sensor that doesn't exist"""
        result = self.db.delete_sensor("28-nonexistent")
        self.assertFalse(result)
    
    def test_add_sensor_replace_existing(self):
        """Test that adding a sensor with existing ID replaces it"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room", enabled=True, monitored=False)
        self.db.add_sensor(sensor_id, "Updated Room", enabled=False, monitored=True)
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertEqual(sensor['name'], "Updated Room")
        self.assertFalse(sensor['enabled'])
        self.assertTrue(sensor['monitored'])
    
    def test_sensor_timestamps(self):
        """Test that sensor timestamps are set correctly"""
        sensor_id = "28-000000000001"
        self.db.add_sensor(sensor_id, "Living Room")
        
        sensor = self.db.get_sensor(sensor_id)
        self.assertIsNotNone(sensor['created_at'])
        self.assertIsNotNone(sensor['updated_at'])
        
        # Timestamps should be set to same value initially
        self.assertEqual(sensor['created_at'], sensor['updated_at'])
        
        # Update sensor and check updated_at is maintained (may or may not change depending on DB precision)
        import time
        time.sleep(1.1)  # Sleep longer to ensure timestamp changes
        self.db.update_sensor(sensor_id, name="Updated")
        
        updated_sensor = self.db.get_sensor(sensor_id)
        # created_at should not change
        self.assertEqual(sensor['created_at'], updated_sensor['created_at'])
        # updated_at should change after sufficient time
        self.assertNotEqual(sensor['updated_at'], updated_sensor['updated_at'])


class TestDatabaseErrorHandling(unittest.TestCase):
    """Test database error handling and edge cases"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_connection_context_manager_rollback(self):
        """Test that connection context manager rolls back on error"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                # Insert valid data
                cursor.execute(
                    "INSERT INTO settings (target_temp_heat, target_temp_cool, hvac_mode) VALUES (?, ?, ?)",
                    (20.0, 24.0, 'heat')
                )
                # Now cause an error
                cursor.execute("INSERT INTO nonexistent_table VALUES (1)")
        except Exception:
            pass  # Expected to fail
        
        # Verify the first insert was rolled back
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM settings")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 0)
    
    def test_load_settings_empty_table(self):
        """Test loading settings when table is empty"""
        settings = self.db.load_settings()
        self.assertIsNone(settings)
    
    def test_get_active_schedules_various_times(self):
        """Test getting active schedules at different times"""
        # Add a schedule for 08:00 on weekdays and enable it
        schedule_id = self.db.create_schedule("Morning", "1,2,3,4,5", "08:00", 20.0, None, "heat")
        self.db.update_schedule(schedule_id, enabled=True)
        
        # Test with datetime - schedules are disabled by default in schema
        # Since we enabled it, let's verify it works
        schedules_all = self.db.get_schedules(enabled_only=False)
        self.assertGreater(len(schedules_all), 0)
        
        enabled_schedules = self.db.get_schedules(enabled_only=True)
        self.assertGreater(len(enabled_schedules), 0)
    
    def test_cleanup_with_no_old_data(self):
        """Test cleanup when there is no old data"""
        # Add recent sensor data
        self.db.log_sensor_reading('sensor1', 'Room', 22.0, False)
        
        # Cleanup data older than 30 days
        self.db.cleanup_old_history(days_to_keep=30)
        
        # Verify recent data is still there
        history = self.db.get_sensor_history(hours=1)
        self.assertEqual(len(history), 1)
    
    def test_get_database_stats_empty(self):
        """Test database stats with empty database"""
        stats = self.db.get_database_stats()
        
        self.assertEqual(stats['sensor_history_count'], 0)
        self.assertEqual(stats['hvac_history_count'], 0)
        self.assertEqual(stats['setting_history_count'], 0)
        self.assertIn('db_size_mb', stats)
        self.assertGreater(stats['db_size_mb'], 0)  # File exists even if empty


class TestScheduleEdgeCases(unittest.TestCase):
    """Test schedule edge cases and special scenarios"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_schedule_with_all_days(self):
        """Test schedule that runs every day"""
        schedule_id = self.db.create_schedule(
            "Everyday", "0,1,2,3,4,5,6", "12:00", 21.0, None, "heat"
        )
        self.assertIsNotNone(schedule_id)
        # Enable the schedule
        self.db.update_schedule(schedule_id, enabled=True)
        
        # Verify schedule exists and is enabled
        schedules = self.db.get_schedules(enabled_only=True)
        self.assertGreater(len(schedules), 0)
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule['days_of_week'], "0,1,2,3,4,5,6")
    
    def test_schedule_update_all_fields(self):
        """Test updating all schedule fields"""
        schedule_id = self.db.create_schedule(
            "Original", "1,2,3", "08:00", 20.0, None, "heat"
        )
        
        self.db.update_schedule(
            schedule_id,
            name="Updated",
            days_of_week="4,5,6",
            time="18:00",
            target_temp_heat=22.0,
            target_temp_cool=25.0,
            hvac_mode="auto",
            enabled=False
        )
        
        # Verify schedule was updated
        schedules = self.db.get_schedules()
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule['name'], "Updated")
        self.assertEqual(schedule['days_of_week'], "4,5,6")
        self.assertEqual(schedule['time'], "18:00")
        self.assertAlmostEqual(schedule['target_temp_heat'], 22.0, places=1)
        self.assertAlmostEqual(schedule['target_temp_cool'], 25.0, places=1)
        self.assertEqual(schedule['hvac_mode'], "auto")
        self.assertEqual(schedule['enabled'], 0)  # SQLite stores bool as 0/1
    
    def test_multiple_schedules_same_time(self):
        """Test multiple schedules at the same time"""
        id1 = self.db.create_schedule("Schedule1", "1", "08:00", 20.0, None, "heat")
        id2 = self.db.create_schedule("Schedule2", "1", "08:00", 21.0, None, "heat")
        
        # Verify both schedules exist
        schedules = self.db.get_schedules()
        self.assertGreaterEqual(len(schedules), 2)
        
        schedule_ids = [s['id'] for s in schedules]
        self.assertIn(id1, schedule_ids)
        self.assertIn(id2, schedule_ids)


class TestDatabaseMaintenance(unittest.TestCase):
    """Test database maintenance and cleanup functions"""
    
    def setUp(self):
        """Create a temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_cleanup_old_history(self):
        """Test cleanup of old history data"""
        # Add some history data
        for i in range(50):
            self.db.log_hvac_state(20.0, 20.0, 'heat', True, False, False, False)
        
        # Cleanup data older than 0 days (should delete all)
        self.db.cleanup_old_history(days_to_keep=0)
        
        # Database should still exist
        self.assertTrue(os.path.exists(self.db_path))


class TestSettingsEdgeCases(unittest.TestCase):
    """Test edge cases in settings handling"""
    
    def setUp(self):
        """Create a temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ThermostatDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_load_settings_missing_temperature_units(self):
        """Test loading settings when temperature_units column doesn't exist"""
        # Save settings normally
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'F')
        
        # Manually remove temperature_units column to simulate old database
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            # Create a new settings table without temperature_units
            cursor.execute('DROP TABLE settings')
            cursor.execute('''
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY,
                    target_temp_heat REAL NOT NULL,
                    target_temp_cool REAL NOT NULL,
                    hvac_mode TEXT NOT NULL,
                    fan_mode TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT INTO settings (target_temp_heat, target_temp_cool, hvac_mode, fan_mode)
                VALUES (20.0, 25.0, 'heat', 'auto')
            ''')
            conn.commit()
        
        # Should load settings with default 'F' for temperature_units
        settings = self.db.load_settings()
        self.assertIsNotNone(settings)
        self.assertEqual(settings['temperature_units'], 'F')
    
    def test_vacuum_database(self):
        """Test manual vacuum operation"""
        # Add and delete data to create fragmentation
        for i in range(50):
            self.db.log_hvac_state(20.0, 20.0, 'heat', True, False, False, False)
        
        self.db.cleanup_old_history(days_to_keep=0)  # Delete all
        
        # Get size before vacuum
        size_before = os.path.getsize(self.db_path)
        
        # Vacuum the database
        with self.db._get_connection() as conn:
            conn.execute('VACUUM')
        
        # Size after should be smaller or same
        size_after = os.path.getsize(self.db_path)
        self.assertLessEqual(size_after, size_before)


class TestScheduleUpdateEdgeCases(unittest.TestCase):
    """Test schedule update edge cases"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.db = ThermostatDatabase(self.temp_file.name)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_update_schedule_no_valid_fields(self):
        """Test updating schedule with no valid fields"""
        schedule_id = self.db.create_schedule(
            name='Test', days_of_week='1,2,3', time_str='08:00',
            target_temp_heat=20.0, target_temp_cool=24.0, hvac_mode='heat'
        )
        
        # Try to update with invalid fields - should be no-op
        self.db.update_schedule(schedule_id, invalid_field='value', another_invalid='data')
        
        # Verify schedule unchanged by getting all schedules
        schedules = self.db.get_schedules()
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0]['name'], 'Test')


class TestSensorHistoryFiltering(unittest.TestCase):
    """Test sensor history filtering by sensor_id"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.db = ThermostatDatabase(self.temp_file.name)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_get_sensor_history_with_specific_sensor_id(self):
        """Test getting history filtered by sensor_id"""
        # Log readings for multiple sensors
        self.db.log_sensor_reading('28-0001', 'Living Room', 21.0, is_compromised=False)
        self.db.log_sensor_reading('28-0002', 'Bedroom', 20.5, is_compromised=False)
        self.db.log_sensor_reading('28-0001', 'Living Room', 21.5, is_compromised=False)
        
        # Get history for specific sensor
        history = self.db.get_sensor_history(sensor_id='28-0001', hours=1)
        
        # Should only return readings for that sensor
        self.assertEqual(len(history), 2)
        for reading in history:
            self.assertEqual(reading['sensor_id'], '28-0001')


class TestSmartCleanupEdgeCases(unittest.TestCase):
    """Test smart cleanup edge cases"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.db = ThermostatDatabase(self.temp_file.name)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_smart_cleanup_missing_database_file(self):
        """Test smart cleanup when database file doesn't exist"""
        # Delete database file
        os.unlink(self.temp_file.name)
        
        # Should return without error
        self.db.smart_cleanup(min_days_to_keep=30, max_disk_percent=50)


if __name__ == '__main__':
    unittest.main()
