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


if __name__ == '__main__':
    unittest.main()
