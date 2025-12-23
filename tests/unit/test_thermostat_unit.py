#!/usr/bin/env python3
"""
Unit tests for thermostat.py
Tests core logic without hardware dependencies
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Mock hardware dependencies before importing
sys.modules['RPi'] = MagicMock()
sys.modules['RPi.GPIO'] = MagicMock()
sys.modules['w1thermsensor'] = MagicMock()

from thermostat import SensorReading, ThermostatController


class TestSensorReading(unittest.TestCase):
    """Test SensorReading class"""
    
    def test_sensor_reading_creation(self):
        """Test creating a sensor reading"""
        now = datetime.now()
        reading = SensorReading('test-id', 'Living Room', 72.5, now)
        
        self.assertEqual(reading.sensor_id, 'test-id')
        self.assertEqual(reading.name, 'Living Room')
        self.assertEqual(reading.temperature, 72.5)
        self.assertEqual(reading.timestamp, now)
        self.assertFalse(reading.is_compromised)
    
    def test_sensor_reading_compromised_flag(self):
        """Test compromised flag can be set"""
        reading = SensorReading('test-id', 'Test', 70.0, datetime.now())
        reading.is_compromised = True
        self.assertTrue(reading.is_compromised)


class TestThermostatController(unittest.TestCase):
    """Test ThermostatController class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'TARGET_TEMP_HEAT': '68.0',
            'TARGET_TEMP_COOL': '74.0',
            'HYSTERESIS': '0.5',
            'SENSOR_READ_INTERVAL': '30',
            'SENSOR_ANOMALY_THRESHOLD': '3.0',
            'SENSOR_DEVIATION_THRESHOLD': '5.0',
            'SENSOR_IGNORE_DURATION': '3600',
            'HVAC_MIN_RUN_TIME': '300',
            'HVAC_MIN_REST_TIME': '300',
            'HVAC_MODE': 'heat',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
            'MONITORED_SENSORS': 'sensor1,sensor2',
            'SENSOR_LIVING_ROOM': 'sensor1',
            'SENSOR_BEDROOM': 'sensor2',
            'LOG_LEVEL': 'ERROR',
            'LOG_FILE': '/tmp/test.log',
            'DATABASE_PATH': ''  # Disable database for unit tests
        })
        self.env_patcher.start()
        
        # Create controller with mocked GPIO
        with patch('thermostat.GPIO', None):
            self.controller = ThermostatController()
    
    def tearDown(self):
        """Clean up after each test"""
        self.env_patcher.stop()
    
    def test_initialization(self):
        """Test controller initializes with correct config"""
        self.assertEqual(self.controller.target_temp_heat, 68.0)
        self.assertEqual(self.controller.target_temp_cool, 74.0)
        self.assertEqual(self.controller.hysteresis, 0.5)
        self.assertEqual(self.controller.hvac_mode, 'heat')
        self.assertEqual(self.controller.sensor_map['sensor1'], 'Living Room')
        self.assertEqual(self.controller.sensor_map['sensor2'], 'Bedroom')
    
    def test_calculate_system_temperature_median(self):
        """Test system temperature calculation uses median"""
        readings = [
            SensorReading('s1', 'Room1', 70.0, datetime.now()),
            SensorReading('s2', 'Room2', 72.0, datetime.now()),
            SensorReading('s3', 'Room3', 74.0, datetime.now()),
        ]
        
        temp = self.controller.calculate_system_temperature(readings)
        self.assertEqual(temp, 72.0)  # Median of [70, 72, 74]
    
    def test_calculate_system_temperature_excludes_compromised(self):
        """Test compromised sensors are excluded from calculation"""
        readings = [
            SensorReading('s1', 'Room1', 70.0, datetime.now()),
            SensorReading('s2', 'Room2', 72.0, datetime.now()),
            SensorReading('s3', 'Room3', 90.0, datetime.now()),  # Anomaly
        ]
        
        # Mark s3 as compromised
        self.controller.compromised_sensors['s3'] = datetime.now() + timedelta(hours=1)
        
        temp = self.controller.calculate_system_temperature(readings)
        self.assertEqual(temp, 71.0)  # Median of [70, 72], excluding 90
    
    def test_calculate_system_temperature_no_valid_readings(self):
        """Test handles case with no valid readings"""
        temp = self.controller.calculate_system_temperature([])
        self.assertIsNone(temp)
    
    def test_is_sensor_compromised(self):
        """Test sensor compromised status check"""
        sensor_id = 'test-sensor'
        
        # Not compromised initially
        self.assertFalse(self.controller._is_sensor_compromised(sensor_id))
        
        # Mark as compromised with future expiry
        future_time = datetime.now() + timedelta(hours=1)
        self.controller.compromised_sensors[sensor_id] = future_time
        self.assertTrue(self.controller._is_sensor_compromised(sensor_id))
        
        # Mark as compromised with past expiry (expired)
        past_time = datetime.now() - timedelta(hours=1)
        self.controller.compromised_sensors[sensor_id] = past_time
        self.assertFalse(self.controller._is_sensor_compromised(sensor_id))
    
    def test_mark_sensor_compromised(self):
        """Test marking sensor as compromised"""
        sensor_id = 'test-sensor'
        self.controller._mark_sensor_compromised(sensor_id, "Test reason")
        
        self.assertIn(sensor_id, self.controller.compromised_sensors)
        self.assertTrue(self.controller._is_sensor_compromised(sensor_id))
    
    def test_detect_anomalies_rapid_change(self):
        """Test anomaly detection for rapid temperature change"""
        sensor_id = 'sensor1'
        
        # Create historical reading from 5 minutes ago
        old_time = datetime.now() - timedelta(minutes=5)
        old_reading = SensorReading(sensor_id, 'Living Room', 70.0, old_time)
        self.controller.sensor_history[sensor_id] = [old_reading]
        
        # Create new reading with rapid increase (>3°F in 5 min)
        new_readings = [
            SensorReading(sensor_id, 'Living Room', 74.0, datetime.now()),
            SensorReading('sensor2', 'Bedroom', 70.0, datetime.now()),
        ]
        
        self.controller.detect_anomalies(new_readings)
        
        # sensor1 should be marked as compromised due to rapid change
        self.assertIn(sensor_id, self.controller.compromised_sensors)
    
    def test_detect_anomalies_deviation_from_average(self):
        """Test anomaly detection for deviation from average"""
        # Ensure sensors are in monitored list and sensor map
        self.controller.monitored_sensors = ['sensor1', 'sensor2']
        self.controller.sensor_map['sensor1'] = 'Living Room'
        self.controller.sensor_map['sensor2'] = 'Bedroom'
        
        readings = [
            SensorReading('sensor1', 'Living Room', 82.0, datetime.now()),  # Very hot!
            SensorReading('sensor2', 'Bedroom', 70.0, datetime.now()),
        ]
        
        self.controller.detect_anomalies(readings)
        
        # sensor1 should be compromised (12°F above 70°F, avg is 76, deviation is 6°F > 5°F threshold)
        self.assertIn('sensor1', self.controller.compromised_sensors)
        self.assertNotIn('sensor2', self.controller.compromised_sensors)
    
    def test_detect_anomalies_clears_expired(self):
        """Test expired compromised sensors are cleared"""
        sensor_id = 'test-sensor'
        
        # Mark sensor as compromised with past expiry
        past_time = datetime.now() - timedelta(hours=1)
        self.controller.compromised_sensors[sensor_id] = past_time
        
        # Run anomaly detection with at least 2 readings (required by function)
        readings = [
            SensorReading('s1', 'Room', 70.0, datetime.now()),
            SensorReading('s2', 'Room2', 71.0, datetime.now())
        ]
        self.controller.detect_anomalies(readings)
        
        # Should be cleared
        self.assertNotIn(sensor_id, self.controller.compromised_sensors)
    
    def test_hvac_state_safety_heat_and_cool(self):
        """Test safety: never activate heat and cool simultaneously"""
        with patch('thermostat.GPIO'):
            # Attempt to set both heat and cool
            self.controller._set_hvac_state(heat=True, cool=True, fan=True)
            
            # Should not change state
            self.assertFalse(self.controller.hvac_state['heat'])
            self.assertFalse(self.controller.hvac_state['cool'])
    
    def test_control_hvac_heating_mode_below_target(self):
        """Test HVAC activates heating when below target"""
        self.controller.hvac_mode = 'heat'
        self.controller.target_temp_heat = 68.0
        self.controller.hysteresis = 0.5
        
        # Temperature below target - hysteresis
        system_temp = 67.0  # Below 68 - 0.5 = 67.5
        
        # Skip minimum time checks for test
        self.controller.last_hvac_change = datetime.now() - timedelta(hours=1)
        
        self.controller.control_hvac(system_temp)
        
        self.assertTrue(self.controller.hvac_state['heat'])
        self.assertTrue(self.controller.hvac_state['fan'])
        self.assertFalse(self.controller.hvac_state['cool'])
    
    def test_control_hvac_heating_mode_above_target(self):
        """Test HVAC deactivates heating when above target"""
        self.controller.hvac_mode = 'heat'
        self.controller.target_temp_heat = 68.0
        self.controller.hysteresis = 0.5
        
        # Temperature above target + hysteresis
        system_temp = 69.0  # Above 68 + 0.5 = 68.5
        
        # Skip minimum time checks
        self.controller.last_hvac_change = datetime.now() - timedelta(hours=1)
        
        self.controller.control_hvac(system_temp)
        
        self.assertFalse(self.controller.hvac_state['heat'])
        self.assertFalse(self.controller.hvac_state['fan'])
    
    def test_control_hvac_secondary_heat(self):
        """Test secondary heat activates when very cold"""
        self.controller.hvac_mode = 'heat'
        self.controller.target_temp_heat = 68.0
        
        # Temperature very low (>3°F below target)
        system_temp = 64.0
        
        # Skip minimum time checks
        self.controller.last_hvac_change = datetime.now() - timedelta(hours=1)
        
        with patch('thermostat.GPIO'):
            self.controller.control_hvac(system_temp)
        
        self.assertTrue(self.controller.hvac_state['heat'])
        self.assertTrue(self.controller.hvac_state['heat2'])
    
    def test_control_hvac_respects_minimum_run_time(self):
        """Test HVAC won't turn off before minimum run time"""
        self.controller.hvac_mode = 'heat'
        self.controller.hvac_min_run_time = 300  # 5 minutes
        
        # Set HVAC running
        self.controller.hvac_state['heat'] = True
        self.controller.last_hvac_change = datetime.now() - timedelta(seconds=60)  # Only 1 min
        
        # Temperature above target (should turn off, but can't due to min run time)
        system_temp = 72.0
        self.controller.control_hvac(system_temp)
        
        # Should still be running
        self.assertTrue(self.controller.hvac_state['heat'])
    
    def test_control_hvac_respects_minimum_rest_time(self):
        """Test HVAC won't turn on before minimum rest time"""
        self.controller.hvac_mode = 'heat'
        self.controller.hvac_min_rest_time = 300  # 5 minutes
        
        # Set HVAC off
        self.controller.hvac_state['heat'] = False
        self.controller.last_hvac_change = datetime.now() - timedelta(seconds=60)  # Only 1 min
        
        # Temperature below target (should turn on, but can't due to min rest time)
        system_temp = 65.0
        self.controller.control_hvac(system_temp)
        
        # Should still be off
        self.assertFalse(self.controller.hvac_state['heat'])
    
    def test_control_hvac_off_mode(self):
        """Test HVAC stays off when mode is 'off'"""
        self.controller.hvac_mode = 'off'
        
        # Temperature way below target
        system_temp = 60.0
        self.controller.control_hvac(system_temp)
        
        self.assertFalse(self.controller.hvac_state['heat'])
        self.assertFalse(self.controller.hvac_state['cool'])
        self.assertFalse(self.controller.hvac_state['fan'])
    
    def test_update_sensor_history(self):
        """Test sensor history is updated and pruned"""
        now = datetime.now()
        
        readings = [
            SensorReading('s1', 'Room1', 70.0, now),
            SensorReading('s2', 'Room2', 72.0, now),
        ]
        
        self.controller.update_sensor_history(readings)
        
        self.assertEqual(len(self.controller.sensor_history['s1']), 1)
        self.assertEqual(len(self.controller.sensor_history['s2']), 1)
        self.assertEqual(self.controller.sensor_history['s1'][0].temperature, 70.0)
    
    def test_update_sensor_history_prunes_old_data(self):
        """Test old history data is pruned (>30 minutes)"""
        sensor_id = 's1'
        
        # Add old reading (>30 minutes ago)
        old_time = datetime.now() - timedelta(minutes=35)
        old_reading = SensorReading(sensor_id, 'Room', 65.0, old_time)
        self.controller.sensor_history[sensor_id] = [old_reading]
        
        # Add new reading
        new_reading = SensorReading(sensor_id, 'Room', 70.0, datetime.now())
        self.controller.update_sensor_history([new_reading])
        
        # Old reading should be pruned
        self.assertEqual(len(self.controller.sensor_history[sensor_id]), 1)
        self.assertEqual(self.controller.sensor_history[sensor_id][0].temperature, 70.0)
    
    def test_get_status(self):
        """Test get_status returns correct information"""
        self.controller.hvac_state['heat'] = True
        self.controller.compromised_sensors['sensor1'] = datetime.now() + timedelta(hours=1)
        
        status = self.controller.get_status()
        
        self.assertEqual(status['hvac_mode'], 'heat')
        self.assertTrue(status['hvac_state']['heat'])
        self.assertEqual(status['target_temp_heat'], 68.0)
        self.assertIn('sensor1', status['compromised_sensors'])
        self.assertEqual(status['sensor_count'], 2)


if __name__ == '__main__':
    unittest.main()
