#!/usr/bin/env python3
"""
Unit tests for web interface Flask routes
Tests API endpoints and page rendering
"""

import unittest
import os
import json
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import web interface components
import web_interface
from web_interface import app, set_control_callback, set_database, update_state


class TestWebInterfaceBasics(unittest.TestCase):
    """Test basic web interface setup"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Set up mock control callback
        self.control_callback = MagicMock(return_value={'success': True})
        set_control_callback(self.control_callback)
    
    def test_index_page_renders(self):
        """Test index page renders without error"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_schedules_page_renders(self):
        """Test schedules page renders"""
        response = self.client.get('/schedules')
        self.assertEqual(response.status_code, 200)
    
    def test_history_page_renders(self):
        """Test history page renders"""
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 200)


class TestAPIStatus(unittest.TestCase):
    """Test API status endpoint"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Reset web interface state to avoid database issues
        import web_interface
        web_interface.database = None
    
    def test_status_endpoint(self):
        """Test /api/status returns current state (converted to Fahrenheit for display)"""
        # Update state first (temperatures in Celsius internally)
        update_state({
            'system_temp': 22.5,  # Celsius
            'target_temp_heat': 20.0,  # Celsius
            'target_temp_cool': 23.33,  # Celsius
            'hvac_mode': 'heat',
            'hvac_state': {'heat': True, 'cool': False, 'fan': True, 'heat2': False},
            'sensor_readings': [],
            'compromised_sensors': [],
        })
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # API returns Fahrenheit for display (22.5°C = 72.5°F)
        self.assertAlmostEqual(data['system_temp'], 72.5, places=1)
        self.assertAlmostEqual(data['target_temp_heat'], 68.0, places=1)
        self.assertEqual(data['hvac_mode'], 'heat')


class TestControlEndpoints(unittest.TestCase):
    """Test control API endpoints"""
    
    def setUp(self):
        """Set up test client and mock callback"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Clear database reference to avoid database errors
        import web_interface
        web_interface.database = None
        
        self.control_callback = MagicMock(return_value={'success': True, 'message': 'OK'})
        set_control_callback(self.control_callback)
    
    def test_set_temperature_heat(self):
        """Test setting heat temperature (converts F to C)"""
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 70})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify callback was called with Celsius value (~21.11°C)
        call_args = self.control_callback.call_args
        self.assertEqual(call_args[0][0], 'set_temperature')
        self.assertEqual(call_args[0][1]['type'], 'heat')
        self.assertAlmostEqual(call_args[0][1]['temperature'], 21.11, places=1)
    
    def test_set_temperature_cool(self):
        """Test setting cool temperature"""
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'cool', 'temperature': 75})
        
        self.assertEqual(response.status_code, 200)
        self.control_callback.assert_called_once()
    
    def test_set_mode(self):
        """Test setting HVAC mode"""
        response = self.client.post('/api/control/mode',
                                   json={'mode': 'cool'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        self.control_callback.assert_called_once_with(
            'set_mode',
            {'mode': 'cool'}
        )
    
    def test_set_fan(self):
        """Test setting fan state"""
        response = self.client.post('/api/control/fan',
                                   json={'fan_on': True})
        
        self.assertEqual(response.status_code, 200)
        self.control_callback.assert_called_once()
    
    def test_control_without_callback(self):
        """Test control endpoints without callback configured"""
        # Remove callback
        set_control_callback(None)
        
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 70})
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_control_callback_error(self):
        """Test handling of control callback errors"""
        # Set callback to raise exception
        error_callback = MagicMock(side_effect=Exception('Test error'))
        set_control_callback(error_callback)
        
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 70})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Test error', data['error'])


class TestScheduleEndpoints(unittest.TestCase):
    """Test schedule management API endpoints"""
    
    def setUp(self):
        """Set up test client with mock database"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import ThermostatDatabase
        self.db = ThermostatDatabase(self.temp_db.name)
        set_database(self.db)
        
        # Mock control callback
        self.control_callback = MagicMock(return_value={'success': True})
        set_control_callback(self.control_callback)
    
    def tearDown(self):
        """Clean up database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_get_schedules(self):
        """Test getting all schedules"""
        # Create a schedule
        self.db.create_schedule("Test", "0,1,2,3,4", "08:00", 68.0, None, "heat")
        
        response = self.client.get('/api/schedules')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('schedules', data)
        schedules = data['schedules']
        self.assertGreater(len(schedules), 0)
        self.assertEqual(schedules[0]['name'], 'Test')
    
    def test_create_schedule(self):
        """Test creating a new schedule"""
        schedule_data = {
            'name': 'Morning',
            'days_of_week': '0,1,2,3,4',
            'time': '06:00',
            'target_temp_heat': 68.0,
            'hvac_mode': 'heat'
        }
        
        response = self.client.post('/api/schedules',
                                   json=schedule_data)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('schedule_id', data)
    
    def test_update_schedule(self):
        """Test updating an existing schedule"""
        # Create schedule first
        schedule_id = self.db.create_schedule("Test", "0,1,2", "08:00", 68.0, None, "heat")
        
        # Update it
        response = self.client.put(f'/api/schedules/{schedule_id}',
                                  json={'name': 'Updated'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        schedules = self.db.get_schedules()
        updated = [s for s in schedules if s['id'] == schedule_id][0]
        self.assertEqual(updated['name'], 'Updated')
    
    def test_delete_schedule(self):
        """Test deleting a schedule"""
        # Create schedule
        schedule_id = self.db.create_schedule("ToDelete", "0,1", "08:00", 68.0, None, "heat")
        
        # Delete it
        response = self.client.delete(f'/api/schedules/{schedule_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify deleted
        schedules = self.db.get_schedules()
        deleted = [s for s in schedules if s['id'] == schedule_id]
        self.assertEqual(len(deleted), 0)
    
    def test_schedule_control_resume(self):
        """Test resuming schedules"""
        response = self.client.post('/api/schedules/control',
                                   json={'action': 'resume'})
        
        self.assertEqual(response.status_code, 200)
        self.control_callback.assert_called_with('resume_schedules', {})
    
    def test_schedule_control_enable(self):
        """Test enabling schedules"""
        response = self.client.post('/api/schedules/control',
                                   json={'action': 'enable'})
        
        self.assertEqual(response.status_code, 200)
        self.control_callback.assert_called_with('set_schedule_enabled', {'enabled': True})
    
    def test_schedule_control_disable(self):
        """Test disabling schedules"""
        response = self.client.post('/api/schedules/control',
                                   json={'action': 'disable'})
        
        self.assertEqual(response.status_code, 200)
        self.control_callback.assert_called_with('set_schedule_enabled', {'enabled': False})
    
    def test_schedule_control_invalid_action(self):
        """Test invalid schedule control action"""
        response = self.client.post('/api/schedules/control',
                                   json={'action': 'invalid'})
        
        self.assertEqual(response.status_code, 400)
    
    def test_schedules_without_database(self):
        """Test schedule endpoints without database"""
        set_database(None)
        
        response = self.client.get('/api/schedules')
        self.assertEqual(response.status_code, 503)


class TestScheduleExceptionHandling(unittest.TestCase):
    """Test schedule endpoint exception handling"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_create_schedule_exception(self):
        """Test exception handling when creating schedule"""
        mock_db = MagicMock()
        mock_db.create_schedule.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.post('/api/schedules',
                                   json={
                                       'name': 'Test',
                                       'days_of_week': '1,2,3',
                                       'time': '08:00'
                                   })
        self.assertEqual(response.status_code, 400)
    
    def test_get_schedules_exception(self):
        """Test exception handling when getting schedules"""
        mock_db = MagicMock()
        mock_db.get_schedules.side_effect = Exception("Database error")
        mock_db.load_settings.return_value = {'temperature_units': 'F'}
        set_database(mock_db)
        
        response = self.client.get('/api/schedules')
        self.assertEqual(response.status_code, 500)
    
    def test_update_schedule_exception(self):
        """Test exception handling when updating schedule"""
        mock_db = MagicMock()
        mock_db.update_schedule.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.put('/api/schedules/1',
                                   json={'name': 'Updated'})
        self.assertEqual(response.status_code, 400)
    
    def test_delete_schedule_exception(self):
        """Test exception handling when deleting schedule"""
        mock_db = MagicMock()
        mock_db.delete_schedule.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.delete('/api/schedules/1')
        self.assertEqual(response.status_code, 400)
    
    def test_schedule_without_database_create(self):
        """Test creating schedule without database"""
        set_database(None)
        
        response = self.client.post('/api/schedules', json={})
        self.assertEqual(response.status_code, 503)
    
    def test_schedule_without_database_update(self):
        """Test updating schedule without database"""
        set_database(None)
        
        response = self.client.put('/api/schedules/1', json={})
        self.assertEqual(response.status_code, 503)
    
    def test_schedule_without_database_delete(self):
        """Test deleting schedule without database"""
        set_database(None)
        
        response = self.client.delete('/api/schedules/1')
        self.assertEqual(response.status_code, 503)
    
    def test_schedule_control_without_callback(self):
        """Test schedule control without callback"""
        set_control_callback(None)
        
        response = self.client.post('/api/schedules/control',
                                   json={'action': 'resume'})
        self.assertEqual(response.status_code, 503)


class TestHistoryEndpoints(unittest.TestCase):
    """Test history API endpoints"""
    
    def setUp(self):
        """Set up test client with database"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import ThermostatDatabase
        self.db = ThermostatDatabase(self.temp_db.name)
        set_database(self.db)
        
        # Add some test data
        self.db.log_sensor_reading('sensor1', 'Living Room', 72.0, False)
        self.db.log_hvac_state(72.0, 68.0, 'heat', True, False, True, False)
        self.db.log_setting_change('hvac_mode', 'off', 'heat', 'web_interface')
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_get_sensor_history(self):
        """Test getting sensor history"""
        response = self.client.get('/api/history/sensors?hours=24')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)
    
    def test_get_hvac_history(self):
        """Test getting HVAC history"""
        response = self.client.get('/api/history/hvac?hours=24')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)
    
    def test_get_settings_history(self):
        """Test getting settings history"""
        response = self.client.get('/api/history/settings?limit=100')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)
    
    def test_get_database_stats(self):
        """Test getting database statistics"""
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('sensor_history_count', data)
        self.assertIn('hvac_history_count', data)
    
    def test_history_without_database(self):
        """Test history endpoints without database"""
        set_database(None)
        
        response = self.client.get('/api/history/sensors')
        self.assertEqual(response.status_code, 503)


class TestAPIEndpoints(unittest.TestCase):
    """Test additional API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Set up database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import ThermostatDatabase
        self.db = ThermostatDatabase(self.temp_db.name)
        set_database(self.db)
        
        # Set default settings
        self.db.save_settings(
            target_temp_heat=20.0,
            target_temp_cool=23.33,
            hvac_mode='heat',
            fan_mode='auto',
            temperature_units='F'
        )
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_api_hvac_endpoint(self):
        """Test HVAC API endpoint"""
        update_state({
            'hvac_mode': 'heat',
            'hvac_state': {'heat': True, 'cool': False, 'fan': True, 'heat2': False},
            'target_temp_heat': 20.0,
            'target_temp_cool': 23.33,
            'system_temp': 21.0
        })
        
        response = self.client.get('/api/hvac')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['mode'], 'heat')
        self.assertIn('state', data)
        self.assertIn('target_heat', data)
    
    def test_control_units_endpoint(self):
        """Test changing temperature units"""
        response = self.client.post('/api/control/units',
                                   json={'units': 'C'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['units'], 'C')
    
    def test_control_units_invalid(self):
        """Test invalid temperature units"""
        response = self.client.post('/api/control/units',
                                   json={'units': 'X'})
        self.assertEqual(response.status_code, 400)
    
    def test_control_units_without_database(self):
        """Test units endpoint without database"""
        set_database(None)
        
        response = self.client.post('/api/control/units',
                                   json={'units': 'C'})
        self.assertEqual(response.status_code, 503)
    
    def test_control_units_exception_handling(self):
        """Test units endpoint exception handling"""
        # Create a mock database that raises an exception
        mock_db = MagicMock()
        mock_db.load_settings.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.post('/api/control/units',
                                   json={'units': 'C'})
        self.assertEqual(response.status_code, 500)
    
    def test_control_units_no_settings(self):
        """Test units endpoint when no settings exist"""
        # Mock database that returns None for settings
        mock_db = MagicMock()
        mock_db.load_settings.return_value = None
        set_database(mock_db)
        
        response = self.client.post('/api/control/units',
                                   json={'units': 'F'})
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('settings', data['error'].lower())
    
    def test_sensors_list_endpoint(self):
        """Test listing sensors from database"""
        # Add some sensors to database
        self.db.add_sensor('28-0001', 'Living Room', enabled=True, monitored=True)
        self.db.add_sensor('28-0002', 'Bedroom', enabled=False, monitored=False)
        
        response = self.client.get('/api/sensors/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('sensors', data)
        self.assertEqual(len(data['sensors']), 2)
    
    def test_sensors_list_without_database(self):
        """Test sensors list without database"""
        set_database(None)
        
        response = self.client.get('/api/sensors/config')
        self.assertEqual(response.status_code, 503)
    
    def test_sensor_update_endpoint(self):
        """Test updating sensor configuration"""
        # Add a sensor first
        self.db.add_sensor('28-0001', 'Living Room', enabled=True, monitored=True)
        
        # Update the sensor
        response = self.client.put('/api/sensors/config/28-0001',
                                   json={
                                       'name': 'Family Room',
                                       'enabled': False,
                                       'monitored': False
                                   })
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        sensor = self.db.get_sensor('28-0001')
        self.assertEqual(sensor['name'], 'Family Room')
        self.assertFalse(sensor['enabled'])
    
    def test_sensor_update_not_found(self):
        """Test updating non-existent sensor"""
        response = self.client.put('/api/sensors/config/28-9999',
                                   json={'name': 'Test'})
        self.assertEqual(response.status_code, 404)
    
    def test_sensor_update_without_database(self):
        """Test sensor update without database"""
        set_database(None)
        
        response = self.client.put('/api/sensors/config/28-0001',
                                   json={'name': 'Test'})
        self.assertEqual(response.status_code, 503)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in web interface"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Reset database to None
        import web_interface
        web_interface.database = None
    
    def test_control_without_callback(self):
        """Test control endpoints without callback configured"""
        set_control_callback(None)
        
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 70})
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_control_invalid_temperature_range(self):
        """Test setting temperature outside valid range"""
        callback = MagicMock(return_value={'success': True})
        set_control_callback(callback)
        
        # Too low (below 50°F)
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 45})
        self.assertEqual(response.status_code, 400)
        
        # Too high (above 90°F)
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'cool', 'temperature': 95})
        self.assertEqual(response.status_code, 400)
    
    def test_control_invalid_mode(self):
        """Test setting invalid HVAC mode"""
        callback = MagicMock(return_value={'success': True})
        set_control_callback(callback)
        
        response = self.client.post('/api/control/mode',
                                   json={'mode': 'turbo'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_control_exception_handling(self):
        """Test exception handling in control endpoints"""
        callback = MagicMock(side_effect=Exception("Test error"))
        set_control_callback(callback)
        
        response = self.client.post('/api/control/fan',
                                   json={'fan_on': True})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_schedule_without_database(self):
        """Test schedule endpoints without database"""
        set_database(None)
        
        response = self.client.get('/api/schedules')
        self.assertEqual(response.status_code, 503)
        
        response = self.client.post('/api/schedules',
                                   json={'name': 'Test', 'enabled': True})
        self.assertEqual(response.status_code, 503)
    
    def test_schedule_exception_handling(self):
        """Test exception handling in schedule endpoints"""
        # Create a mock database that raises an exception
        mock_db = MagicMock()
        mock_db.create_schedule.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.post('/api/schedules',
                                   json={
                                       'name': 'Test Schedule',
                                       'enabled': True,
                                       'days': [0, 1, 2, 3, 4],
                                       'time': '08:00',
                                       'settings': {}
                                   })
        self.assertEqual(response.status_code, 400)
    
    def test_sensors_endpoint(self):
        """Test sensors endpoint with sensor data"""
        # Update state with sensor readings
        update_state({
            'sensor_readings': [
                {'id': 's1', 'name': 'Living Room', 'temperature': 72.0, 'timestamp': datetime.now().isoformat()},
                {'id': 's2', 'name': 'Bedroom', 'temperature': 70.0, 'timestamp': datetime.now().isoformat()}
            ]
        })
        
        response = self.client.get('/api/sensors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('sensors', data)
        self.assertEqual(len(data['sensors']), 2)
    
    def test_hvac_state_in_status(self):
        """Test HVAC state is included in status endpoint"""
        update_state({
            'hvac_state': {
                'heat': True,
                'cool': False,
                'fan': True,
                'heat2': False
            }
        })
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('hvac_state', data)
        self.assertTrue(data['hvac_state']['heat'])
        self.assertFalse(data['hvac_state']['cool'])
        self.assertTrue(data['hvac_state']['fan'])


class TestTemperatureUnitConversions(unittest.TestCase):
    """Test temperature unit conversions in API responses"""
    
    def setUp(self):
        """Set up test client with database"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temp database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import ThermostatDatabase
        self.db = ThermostatDatabase(self.temp_db.name)
        set_database(self.db)
        
        # Add units setting via save_settings
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'C')
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_status_with_celsius_conversion(self):
        """Test status endpoint converts temperatures to Celsius when units='C'"""
        update_state({
            'system_temp': 20.0,  # Celsius internally
            'target_temp_heat': 18.0,
            'sensor_readings': [
                {'sensor_id': '28-0001', 'temperature': 19.5, 'compromised': False}
            ]
        })
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Should stay in Celsius
        self.assertAlmostEqual(data['system_temp'], 20.0, places=1)
        self.assertEqual(len(data['sensor_readings']), 1)
        self.assertAlmostEqual(data['sensor_readings'][0]['temperature'], 19.5, places=1)
    
    def test_status_with_kelvin_conversion(self):
        """Test status endpoint converts temperatures to Kelvin when units='K'"""
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'K')
        
        update_state({
            'system_temp': 20.0,  # Celsius internally
            'sensor_readings': [
                {'sensor_id': '28-0001', 'temperature': 19.5, 'compromised': False}
            ]
        })
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Should convert to Kelvin (20°C = 293.15K)
        self.assertAlmostEqual(data['system_temp'], 293.15, places=1)
        self.assertAlmostEqual(data['sensor_readings'][0]['temperature'], 292.65, places=1)
    
    def test_control_temperature_celsius_validation(self):
        """Test temperature validation for Celsius units"""
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'C')
        
        # Mock control callback
        control_callback = MagicMock(return_value={'success': True})
        set_control_callback(control_callback)
        
        # Try to set valid Celsius temperature
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 20})
        self.assertEqual(response.status_code, 200)
        
        # Try to set temperature out of range for Celsius (should be 10-32)
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 5})
        self.assertEqual(response.status_code, 400)
    
    def test_control_temperature_kelvin_validation(self):
        """Test temperature validation for Kelvin units"""
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'K')
        
        # Mock control callback
        control_callback = MagicMock(return_value={'success': True})
        set_control_callback(control_callback)
        
        # Try to set valid Kelvin temperature
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 293})
        self.assertEqual(response.status_code, 200)
        
        # Try to set temperature out of range for Kelvin (should be 283-305)
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 250})
        self.assertEqual(response.status_code, 400)
    
    def test_schedule_create_with_unit_conversion(self):
        """Test schedule creation converts temperatures from display units to Celsius"""
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'F')
        
        response = self.client.post('/api/schedules',
                                   json={
                                       'name': 'Test',
                                       'days_of_week': '0,1,2',
                                       'time': '08:00',
                                       'target_temp_heat': 70.0,  # Fahrenheit
                                       'target_temp_cool': 75.0,  # Fahrenheit
                                       'hvac_mode': 'auto'
                                   })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify stored in Celsius
        schedules = self.db.get_schedules()
        self.assertEqual(len(schedules), 1)
        # 70°F ≈ 21.1°C, 75°F ≈ 23.9°C
        self.assertAlmostEqual(schedules[0]['target_temp_heat'], 21.1, places=1)
        self.assertAlmostEqual(schedules[0]['target_temp_cool'], 23.9, places=1)
    
    def test_schedule_update_with_unit_conversion(self):
        """Test schedule update converts temperatures from display units"""
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'F')
        
        # Create schedule in Celsius
        schedule_id = self.db.create_schedule("Test", "0,1", "08:00", 20.0, 25.0, "auto")
        
        # Update with Fahrenheit values
        response = self.client.put(f'/api/schedules/{schedule_id}',
                                  json={
                                      'target_temp_heat': 72.0,  # Fahrenheit
                                      'target_temp_cool': 78.0   # Fahrenheit
                                  })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify stored in Celsius
        schedules = self.db.get_schedules()
        updated = [s for s in schedules if s['id'] == schedule_id][0]
        # 72°F ≈ 22.2°C, 78°F ≈ 25.6°C
        self.assertAlmostEqual(updated['target_temp_heat'], 22.2, places=1)
        self.assertAlmostEqual(updated['target_temp_cool'], 25.6, places=1)
    
    def test_schedules_get_with_unit_conversion(self):
        """Test getting schedules converts to display units"""
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'F')
        
        # Create schedule in Celsius (internal storage)
        self.db.create_schedule("Test", "0,1", "08:00", 20.0, 25.0, "auto")
        
        response = self.client.get('/api/schedules')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        schedules = data['schedules']
        self.assertEqual(len(schedules), 1)
        
        # Should be converted to Fahrenheit
        # 20°C ≈ 68°F, 25°C ≈ 77°F
        self.assertAlmostEqual(schedules[0]['target_temp_heat'], 68.0, places=0)
        self.assertAlmostEqual(schedules[0]['target_temp_cool'], 77.0, places=0)


class TestSensorHistoryEndpoints(unittest.TestCase):
    """Test sensor history database endpoints"""
    
    def setUp(self):
        """Set up test client with database"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temp database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import ThermostatDatabase
        self.db = ThermostatDatabase(self.temp_db.name)
        set_database(self.db)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_history_sensors_without_database(self):
        """Test /api/history/sensors returns 503 without database"""
        set_database(None)
        
        response = self.client.get('/api/history/sensors')
        self.assertEqual(response.status_code, 503)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_history_sensors_exception_handling(self):
        """Test /api/history/sensors handles exceptions"""
        # Create mock that raises exception
        mock_db = MagicMock()
        mock_db.get_sensor_history.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.get('/api/history/sensors')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_database_stats_without_database(self):
        """Test /api/database/stats returns 503 without database"""
        set_database(None)
        
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 503)
    
    def test_database_stats_exception_handling(self):
        """Test /api/database/stats handles exceptions"""
        mock_db = MagicMock()
        mock_db.get_database_size.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 500)


class TestFanControlEndpoints(unittest.TestCase):
    """Test fan control without callback"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Clear database and callback
        set_database(None)
        set_control_callback(None)
    
    def test_fan_control_without_callback(self):
        """Test /api/control/fan returns 503 without callback"""
        response = self.client.post('/api/control/fan',
                                   json={'fan_on': True})
        
        self.assertEqual(response.status_code, 503)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_mode_control_without_callback(self):
        """Test /api/control/mode returns 503 without callback"""
        response = self.client.post('/api/control/mode',
                                   json={'mode': 'heat'})
        
        self.assertEqual(response.status_code, 503)
    
    def test_mode_control_exception_handling(self):
        """Test /api/control/mode handles exceptions"""
        error_callback = MagicMock(side_effect=Exception("Control error"))
        set_control_callback(error_callback)
        
        response = self.client.post('/api/control/mode',
                                   json={'mode': 'heat'})
        
        self.assertEqual(response.status_code, 400)


class TestSensorConfigEndpoints(unittest.TestCase):
    """Test sensor configuration CRUD endpoints"""
    
    def setUp(self):
        """Set up test client with database"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temp database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import ThermostatDatabase
        self.db = ThermostatDatabase(self.temp_db.name)
        set_database(self.db)
        
        # Mock control callback
        self.control_callback = MagicMock()
        set_control_callback(self.control_callback)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_get_sensor_configs_exception(self):
        """Test /api/sensors/config handles exceptions"""
        mock_db = MagicMock()
        mock_db.get_sensors.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.get('/api/sensors/config')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_update_sensor_config_exception(self):
        """Test /api/sensors/config/<id> PUT handles exceptions"""
        mock_db = MagicMock()
        mock_db.update_sensor.side_effect = Exception("Update error")
        set_database(mock_db)
        
        response = self.client.put('/api/sensors/config/28-0001',
                                   json={'name': 'Test'})
        self.assertEqual(response.status_code, 500)
    
    def test_update_sensor_with_reload_callback(self):
        """Test sensor update triggers reload callback"""
        # Add sensor first
        self.db.add_sensor('28-0001', 'Living Room', enabled=True, monitored=True)
        
        response = self.client.put('/api/sensors/config/28-0001',
                                   json={'name': 'Family Room'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify callback was called with reload action
        self.control_callback.assert_called_once()
        call_args = self.control_callback.call_args[0][0]
        self.assertEqual(call_args['action'], 'reload_sensors')
    
    def test_delete_sensor_config_without_database(self):
        """Test DELETE /api/sensors/config/<id> without database"""
        set_database(None)
        
        response = self.client.delete('/api/sensors/config/28-0001')
        self.assertEqual(response.status_code, 503)
    
    def test_delete_sensor_config_not_found(self):
        """Test deleting non-existent sensor returns 404"""
        response = self.client.delete('/api/sensors/config/28-9999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('not found', data['error'].lower())
    
    def test_delete_sensor_config_success(self):
        """Test successful sensor deletion"""
        # Add sensor first
        self.db.add_sensor('28-0001', 'Living Room', enabled=True, monitored=True)
        
        response = self.client.delete('/api/sensors/config/28-0001')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['sensor_id'], '28-0001')
        
        # Verify callback was called
        self.control_callback.assert_called_once()
    
    def test_delete_sensor_config_exception(self):
        """Test DELETE /api/sensors/config/<id> handles exceptions"""
        mock_db = MagicMock()
        mock_db.delete_sensor.side_effect = Exception("Delete error")
        set_database(mock_db)
        
        response = self.client.delete('/api/sensors/config/28-0001')
        self.assertEqual(response.status_code, 500)


class TestHistoryEndpointsException(unittest.TestCase):
    """Test history endpoint exception handling"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_hvac_history_without_database(self):
        """Test /api/history/hvac without database"""
        set_database(None)
        
        response = self.client.get('/api/history/hvac')
        self.assertEqual(response.status_code, 503)
    
    def test_hvac_history_exception(self):
        """Test /api/history/hvac handles exceptions"""
        mock_db = MagicMock()
        mock_db.get_hvac_history.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.get('/api/history/hvac')
        self.assertEqual(response.status_code, 500)
    
    def test_settings_history_without_database(self):
        """Test /api/history/settings without database"""
        set_database(None)
        
        response = self.client.get('/api/history/settings')
        self.assertEqual(response.status_code, 503)
    
    def test_settings_history_exception(self):
        """Test /api/history/settings handles exceptions"""
        mock_db = MagicMock()
        mock_db.get_setting_history.side_effect = Exception("Database error")
        set_database(mock_db)
        
        response = self.client.get('/api/history/settings')
        self.assertEqual(response.status_code, 500)


class TestSettingsPage(unittest.TestCase):
    """Test settings page and related endpoints"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Set up mock database
        self.mock_db = MagicMock()
        set_database(self.mock_db)
        
        # Set up mock control callback
        self.control_callback = MagicMock(return_value={'success': True})
        set_control_callback(self.control_callback)
    
    def test_settings_page_renders(self):
        """Test settings page renders without error"""
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Settings', response.data)
    
    def test_get_sensor_configs(self):
        """Test getting sensor configurations"""
        self.mock_db.get_sensors.return_value = [
            {'sensor_id': '28-001', 'name': 'Living Room', 'enabled': True, 'monitored': True},
            {'sensor_id': '28-002', 'name': 'Bedroom', 'enabled': True, 'monitored': False}
        ]
        
        response = self.client.get('/api/sensors/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['sensors']), 2)
        self.assertEqual(data['sensors'][0]['name'], 'Living Room')
    
    def test_get_sensor_configs_without_database(self):
        """Test getting sensor configs without database"""
        set_database(None)
        
        response = self.client.get('/api/sensors/config')
        self.assertEqual(response.status_code, 503)
    
    def test_update_sensor_config(self):
        """Test updating sensor configuration"""
        self.mock_db.update_sensor.return_value = True
        
        response = self.client.put('/api/sensors/config/28-001',
                                   data=json.dumps({
                                       'name': 'New Name',
                                       'enabled': True,
                                       'monitored': False
                                   }),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.mock_db.update_sensor.assert_called_once_with(
            '28-001',
            name='New Name',
            enabled=True,
            monitored=False
        )
    
    def test_update_sensor_config_not_found(self):
        """Test updating non-existent sensor"""
        self.mock_db.update_sensor.return_value = False
        
        response = self.client.put('/api/sensors/config/28-999',
                                   data=json.dumps({'name': 'Test'}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_sensor_config(self):
        """Test deleting sensor configuration"""
        self.mock_db.delete_sensor.return_value = True
        
        response = self.client.delete('/api/sensors/config/28-001')
        
        self.assertEqual(response.status_code, 200)
        self.mock_db.delete_sensor.assert_called_once_with('28-001')
    
    def test_delete_sensor_config_not_found(self):
        """Test deleting non-existent sensor"""
        self.mock_db.delete_sensor.return_value = False
        
        response = self.client.delete('/api/sensors/config/28-999')
        
        self.assertEqual(response.status_code, 404)
    
    def test_get_database_stats(self):
        """Test getting database statistics"""
        self.mock_db.get_database_stats.return_value = {
            'database_path': '/path/to/db.sqlite',
            'database_size_bytes': 1048576,
            'sensor_history_count': 5000,
            'hvac_history_count': 1000
        }
        
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['database_size_bytes'], 1048576)
        self.assertEqual(data['sensor_history_count'], 5000)
    
    def test_get_database_stats_without_database(self):
        """Test getting stats without database"""
        set_database(None)
        
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 503)


if __name__ == '__main__':
    unittest.main()
