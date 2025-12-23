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
    
    def test_status_endpoint(self):
        """Test /api/status returns current state"""
        # Update state first
        update_state({
            'system_temp': 72.5,
            'target_temp_heat': 68.0,
            'target_temp_cool': 74.0,
            'hvac_mode': 'heat',
            'hvac_state': {'heat': True, 'cool': False, 'fan': True, 'heat2': False},
            'sensor_readings': [],
            'compromised_sensors': [],
        })
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['system_temp'], 72.5)
        self.assertEqual(data['target_temp_heat'], 68.0)
        self.assertEqual(data['hvac_mode'], 'heat')


class TestControlEndpoints(unittest.TestCase):
    """Test control API endpoints"""
    
    def setUp(self):
        """Set up test client and mock callback"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        self.control_callback = MagicMock(return_value={'success': True, 'message': 'OK'})
        set_control_callback(self.control_callback)
    
    def test_set_temperature_heat(self):
        """Test setting heat temperature"""
        response = self.client.post('/api/control/temperature',
                                   json={'type': 'heat', 'temperature': 70})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify callback was called
        self.control_callback.assert_called_once_with(
            'set_temperature',
            {'type': 'heat', 'temperature': 70}
        )
    
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


if __name__ == '__main__':
    unittest.main()
