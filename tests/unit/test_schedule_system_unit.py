#!/usr/bin/env python3
"""
Unit tests for schedule system and database integration
Tests schedule checking, hold functionality, and history logging
"""

import unittest
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Mock hardware dependencies before importing
sys.modules['RPi'] = MagicMock()
sys.modules['RPi.GPIO'] = MagicMock()
sys.modules['w1thermsensor'] = MagicMock()

from thermostat import ThermostatController


class TestScheduleSystem(unittest.TestCase):
    """Test schedule checking and execution"""
    
    def setUp(self):
        """Set up test environment with database"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Mock environment with database enabled
        self.env_patcher = patch.dict(os.environ, {
            'TARGET_TEMP_HEAT': '68.0',
            'TARGET_TEMP_COOL': '74.0',
            'HYSTERESIS': '0.5',
            'HVAC_MODE': 'heat',
            'DATABASE_PATH': self.db_path,
            'SCHEDULE_ENABLED': 'true',
            'SCHEDULE_HOLD_HOURS': '2',
            'LOG_LEVEL': 'ERROR',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
        })
        self.env_patcher.start()
        
        # Create controller with mocked GPIO
        with patch('thermostat.GPIO', None):
            self.controller = ThermostatController()
    
    def tearDown(self):
        """Clean up"""
        self.env_patcher.stop()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_schedule_checking_enabled(self):
        """Test that schedules are checked when enabled"""
        # Create a schedule for current time
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 70.0, None, "heat"
        )
        
        # Check schedules
        self.controller._check_schedules(now)
        
        # Verify temperature was updated
        self.assertEqual(self.controller.target_temp_heat, 70.0)
    
    def test_schedule_checking_disabled(self):
        """Test that schedules are ignored when disabled"""
        # Disable schedules
        self.controller.schedule_enabled = False
        
        # Create a schedule
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 75.0, None, "heat"
        )
        
        original_temp = self.controller.target_temp_heat
        
        # Check schedules
        self.controller._check_schedules(now)
        
        # Verify temperature was NOT updated
        self.assertEqual(self.controller.target_temp_heat, original_temp)
    
    def test_schedule_hold_blocks_execution(self):
        """Test that schedule hold prevents schedule execution"""
        # Set hold for 1 hour from now
        self.controller.schedule_hold_until = datetime.now() + timedelta(hours=1)
        
        # Create a schedule for now
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 75.0, None, "heat"
        )
        
        original_temp = self.controller.target_temp_heat
        
        # Check schedules
        self.controller._check_schedules(now)
        
        # Verify temperature was NOT updated (hold is active)
        self.assertEqual(self.controller.target_temp_heat, original_temp)
    
    def test_expired_schedule_hold_clears(self):
        """Test that expired holds are cleared"""
        # Set hold that expired 1 hour ago
        self.controller.schedule_hold_until = datetime.now() - timedelta(hours=1)
        
        # Create a schedule for now
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 72.0, None, "heat"
        )
        
        # Check schedules
        self.controller._check_schedules(now)
        
        # Verify hold was cleared
        self.assertIsNone(self.controller.schedule_hold_until)
        
        # Verify schedule was applied
        self.assertEqual(self.controller.target_temp_heat, 72.0)
    
    def test_set_schedule_hold(self):
        """Test setting schedule hold when schedules exist"""
        # Create a schedule first
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 70.0, None, "heat"
        )
        
        before = datetime.now()
        self.controller._set_schedule_hold()
        after = datetime.now()
        
        # Verify hold is set
        self.assertIsNotNone(self.controller.schedule_hold_until)
        
        # Verify hold is approximately 2 hours from now
        expected_hold = datetime.now() + timedelta(hours=2)
        time_diff = abs((self.controller.schedule_hold_until - expected_hold).total_seconds())
        self.assertLess(time_diff, 10)  # Within 10 seconds
    
    def test_resume_schedules(self):
        """Test resume schedules clears hold"""
        # Set a hold
        self.controller.schedule_hold_until = datetime.now() + timedelta(hours=1)
        
        # Resume schedules
        result = self.controller.resume_schedules()
        
        self.assertTrue(result['success'])
        self.assertIsNone(self.controller.schedule_hold_until)
    
    def test_set_schedule_enabled(self):
        """Test enabling/disabling schedules"""
        # Disable
        result = self.controller.set_schedule_enabled(False)
        self.assertTrue(result['success'])
        self.assertFalse(self.controller.schedule_enabled)
        
        # Enable
        result = self.controller.set_schedule_enabled(True)
        self.assertTrue(result['success'])
        self.assertTrue(self.controller.schedule_enabled)
    
    def test_schedule_updates_multiple_settings(self):
        """Test schedule can update heat, cool, and mode"""
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 70.0, 76.0, "auto"
        )
        
        # Check schedules
        self.controller._check_schedules(now)
        
        # Verify all settings updated
        self.assertEqual(self.controller.target_temp_heat, 70.0)
        self.assertEqual(self.controller.target_temp_cool, 76.0)
        self.assertEqual(self.controller.hvac_mode, 'auto')


class TestHistoryLogging(unittest.TestCase):
    """Test history logging functionality"""
    
    def setUp(self):
        """Set up test environment with database"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Mock environment with database enabled
        self.env_patcher = patch.dict(os.environ, {
            'TARGET_TEMP_HEAT': '68.0',
            'TARGET_TEMP_COOL': '74.0',
            'DATABASE_PATH': self.db_path,
            'HISTORY_LOG_INTERVAL': '300',
            'LOG_LEVEL': 'ERROR',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
        })
        self.env_patcher.start()
        
        # Create controller with mocked GPIO
        with patch('thermostat.GPIO', None):
            self.controller = ThermostatController()
    
    def tearDown(self):
        """Clean up"""
        self.env_patcher.stop()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_log_sensor_history(self):
        """Test sensor readings are logged to database"""
        from thermostat import SensorReading
        
        # Create some sensor readings
        readings = [
            SensorReading('sensor1', 'Living Room', 72.0, datetime.now()),
            SensorReading('sensor2', 'Bedroom', 70.5, datetime.now()),
        ]
        
        # Log to database
        self.controller._log_sensor_history(readings)
        
        # Verify logged
        history = self.controller.db.get_sensor_history(hours=1)
        self.assertEqual(len(history), 2)
        
        temps = [h['temperature'] for h in history]
        self.assertIn(72.0, temps)
        self.assertIn(70.5, temps)
    
    def test_log_sensor_history_includes_compromised_flag(self):
        """Test compromised sensors are logged correctly"""
        from thermostat import SensorReading
        
        reading = SensorReading('sensor1', 'Test', 75.0, datetime.now())
        reading.is_compromised = True
        
        self.controller._log_sensor_history([reading])
        
        history = self.controller.db.get_sensor_history(hours=1)
        self.assertEqual(history[0]['is_compromised'], 1)
    
    def test_log_hvac_history(self):
        """Test HVAC state is logged to database"""
        # Set some state
        self.controller.hvac_state = {
            'heat': True,
            'cool': False,
            'fan': True,
            'heat2': False
        }
        self.controller.latest_system_temp = 72.5
        self.controller.hvac_mode = 'heat'
        
        # Log to database
        self.controller._log_hvac_history(72.5)
        
        # Verify logged
        history = self.controller.db.get_hvac_history(hours=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['hvac_mode'], 'heat')
        self.assertEqual(history[0]['heat_active'], 1)
        self.assertEqual(history[0]['fan_active'], 1)
        self.assertEqual(history[0]['system_temp'], 72.5)
    
    def test_history_logging_without_database(self):
        """Test history logging gracefully handles missing database"""
        # Remove database
        self.controller.db = None
        
        from thermostat import SensorReading
        readings = [SensorReading('s1', 'Test', 70.0, datetime.now())]
        
        # Should not raise exception
        self.controller._log_sensor_history(readings)
        self.controller._log_hvac_history(70.0)


class TestDatabaseIntegration(unittest.TestCase):
    """Test database integration paths"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_controller_loads_persisted_settings(self):
        """Test controller loads settings from database on init"""
        from database import ThermostatDatabase
        
        # Create database and save settings
        db = ThermostatDatabase(self.db_path)
        db.save_settings(72.0, 78.0, 'cool')
        
        # Create controller with that database
        env_patcher = patch.dict(os.environ, {
            'TARGET_TEMP_HEAT': '68.0',  # Will be overridden by DB
            'TARGET_TEMP_COOL': '74.0',  # Will be overridden by DB
            'HVAC_MODE': 'heat',  # Will be overridden by DB
            'DATABASE_PATH': self.db_path,
            'LOG_LEVEL': 'ERROR',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
        })
        
        with env_patcher:
            with patch('thermostat.GPIO', None):
                controller = ThermostatController()
        
        # Verify settings were loaded from database
        self.assertEqual(controller.target_temp_heat, 72.0)
        self.assertEqual(controller.target_temp_cool, 78.0)
        self.assertEqual(controller.hvac_mode, 'cool')
    
    def test_controller_without_database(self):
        """Test controller works without database"""
        env_patcher = patch.dict(os.environ, {
            'TARGET_TEMP_HEAT': '68.0',  # Config in Fahrenheit, stored as Celsius
            'TARGET_TEMP_COOL': '74.0',
            'DATABASE_PATH': '',  # No database
            'LOG_LEVEL': 'ERROR',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
        })
        
        with env_patcher:
            with patch('thermostat.GPIO', None):
                controller = ThermostatController()
        
        # Should use env defaults (converted to Celsius)
        self.assertAlmostEqual(controller.target_temp_heat, 20.0, places=1)  # 68°F = 20°C
        self.assertAlmostEqual(controller.target_temp_cool, 23.33, places=1)  # 74°F = 23.33°C
        self.assertIsNone(controller.db)


class TestWebControlWithScheduleHold(unittest.TestCase):
    """Test web control commands trigger schedule hold"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        self.env_patcher = patch.dict(os.environ, {
            'TARGET_TEMP_HEAT': '68.0',
            'TARGET_TEMP_COOL': '74.0',
            'DATABASE_PATH': self.db_path,
            'SCHEDULE_HOLD_HOURS': '2',
            'LOG_LEVEL': 'ERROR',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
        })
        self.env_patcher.start()
        
        with patch('thermostat.GPIO', None):
            self.controller = ThermostatController()
    
    def tearDown(self):
        """Clean up"""
        self.env_patcher.stop()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_set_temperature_triggers_hold(self):
        """Test setting temperature via web triggers schedule hold when schedules exist"""
        # Create a schedule first
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 20.0, None, "heat"
        )
        
        result = self.controller.handle_control_command(
            'set_temperature',
            {'type': 'heat', 'temperature': 22}  # Celsius
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(self.controller.schedule_hold_until)
    
    def test_set_mode_triggers_hold(self):
        """Test setting mode via web triggers schedule hold when schedules exist"""
        # Create a schedule first
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        weekday = str(now.weekday())
        
        self.controller.db.create_schedule(
            "Test Schedule", weekday, time_str, 20.0, None, "heat"
        )
        
        result = self.controller.handle_control_command(
            'set_mode',
            {'mode': 'cool'}
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(self.controller.schedule_hold_until)
    
    def test_resume_schedules_command(self):
        """Test resume_schedules control command"""
        # Set hold
        self.controller.schedule_hold_until = datetime.now() + timedelta(hours=1)
        
        # Resume via command
        result = self.controller.handle_control_command('resume_schedules', {})
        
        self.assertTrue(result['success'])
        self.assertIsNone(self.controller.schedule_hold_until)
    
    def test_set_schedule_enabled_command(self):
        """Test set_schedule_enabled control command"""
        # Disable
        result = self.controller.handle_control_command(
            'set_schedule_enabled',
            {'enabled': False}
        )
        
        self.assertTrue(result['success'])
        self.assertFalse(self.controller.schedule_enabled)
        
        # Enable
        result = self.controller.handle_control_command(
            'set_schedule_enabled',
            {'enabled': True}
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(self.controller.schedule_enabled)
    
    def test_get_status_includes_schedule_info(self):
        """Test status includes schedule state"""
        status = self.controller.get_status()
        
        self.assertIn('schedule_enabled', status)
        self.assertIn('schedule_on_hold', status)
        
        # Set hold and verify it's in status
        self.controller.schedule_hold_until = datetime.now() + timedelta(hours=1)
        status = self.controller.get_status()
        
        self.assertTrue(status['schedule_on_hold'])
        self.assertIn('schedule_hold_until', status)


if __name__ == '__main__':
    unittest.main()
