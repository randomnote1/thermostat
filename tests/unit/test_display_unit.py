#!/usr/bin/env python3
"""
Unit tests for display.py
Tests display logic without hardware dependencies
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Mock hardware dependencies
sys.modules['waveshare_epd'] = MagicMock()
sys.modules['waveshare_epd.epd2in13_V2'] = MagicMock()

from display import ThermostatDisplay


class TestThermostatDisplay(unittest.TestCase):
    """Test ThermostatDisplay class"""
    
    def setUp(self):
        """Set up test environment"""
        with patch('display.DISPLAY_AVAILABLE', False):
            self.display = ThermostatDisplay()
    
    def test_initialization(self):
        """Test display initializes with correct dimensions"""
        self.assertEqual(self.display.width, 250)
        self.assertEqual(self.display.height, 122)
    
    def test_create_display_image_basic(self):
        """Test creating a basic display image"""
        hvac_state = {'heat': True, 'cool': False, 'fan': True, 'heat2': False}
        
        image = self.display.create_display_image(
            system_temp=70.5,
            target_temp=68.0,
            hvac_state=hvac_state,
            sensor_readings=[],
            compromised_sensors=[]
        )
        
        # Verify image was created with correct size (rotated)
        self.assertEqual(image.size, (self.display.height, self.display.width))
    
    def test_create_display_image_with_sensors(self):
        """Test creating display with sensor readings"""
        from thermostat import SensorReading
        
        hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        sensor_readings = [
            SensorReading('s1', 'Living Room', 70.0, datetime.now()),
            SensorReading('s2', 'Bedroom', 72.0, datetime.now()),
        ]
        
        image = self.display.create_display_image(
            system_temp=71.0,
            target_temp=68.0,
            hvac_state=hvac_state,
            sensor_readings=sensor_readings,
            compromised_sensors=[]
        )
        
        self.assertIsNotNone(image)
    
    def test_create_display_image_with_compromised_sensors(self):
        """Test display marks compromised sensors"""
        from thermostat import SensorReading
        
        hvac_state = {'heat': True, 'cool': False, 'fan': True, 'heat2': False}
        sensor_readings = [
            SensorReading('s1', 'Living Room', 85.0, datetime.now()),
            SensorReading('s2', 'Bedroom', 70.0, datetime.now()),
        ]
        compromised_sensors = ['s1']
        
        image = self.display.create_display_image(
            system_temp=72.5,
            target_temp=68.0,
            hvac_state=hvac_state,
            sensor_readings=sensor_readings,
            compromised_sensors=compromised_sensors
        )
        
        self.assertIsNotNone(image)
    
    def test_create_display_image_hvac_states(self):
        """Test display shows different HVAC states"""
        from thermostat import SensorReading
        
        test_cases = [
            {'heat': True, 'cool': False, 'fan': True, 'heat2': False},
            {'heat': False, 'cool': True, 'fan': True, 'heat2': False},
            {'heat': False, 'cool': False, 'fan': False, 'heat2': False},
            {'heat': True, 'cool': False, 'fan': True, 'heat2': True},
        ]
        
        for hvac_state in test_cases:
            image = self.display.create_display_image(
                system_temp=70.0,
                target_temp=68.0,
                hvac_state=hvac_state,
                sensor_readings=[],
                compromised_sensors=[]
            )
            self.assertIsNotNone(image)
    
    def test_create_display_image_truncates_long_sensor_names(self):
        """Test long sensor names are truncated"""
        from thermostat import SensorReading
        
        hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        sensor_readings = [
            SensorReading('s1', 'Very Long Sensor Name That Should Be Truncated', 70.0, datetime.now()),
        ]
        
        # Should not raise an exception
        image = self.display.create_display_image(
            system_temp=70.0,
            target_temp=68.0,
            hvac_state=hvac_state,
            sensor_readings=sensor_readings,
            compromised_sensors=[]
        )
        
        self.assertIsNotNone(image)
    
    def test_create_display_image_limits_sensor_count(self):
        """Test only shows up to 5 sensors"""
        from thermostat import SensorReading
        
        hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        
        # Create 10 sensors
        sensor_readings = [
            SensorReading(f's{i}', f'Room{i}', 70.0 + i, datetime.now())
            for i in range(10)
        ]
        
        # Should handle gracefully (display only shows 5)
        image = self.display.create_display_image(
            system_temp=75.0,
            target_temp=68.0,
            hvac_state=hvac_state,
            sensor_readings=sensor_readings,
            compromised_sensors=[]
        )
        
        self.assertIsNotNone(image)
    
    def test_update_without_display(self):
        """Test update gracefully handles missing display"""
        hvac_state = {'heat': True, 'cool': False, 'fan': True, 'heat2': False}
        
        # Display not available
        result = self.display.update(
            system_temp=70.0,
            target_temp=68.0,
            hvac_state=hvac_state
        )
        
        # Should return False but not crash
        self.assertFalse(result)
    
    def test_update_with_defaults(self):
        """Test update handles None for optional parameters"""
        hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        
        # Should not crash with None values
        result = self.display.update(
            system_temp=70.0,
            target_temp=68.0,
            hvac_state=hvac_state,
            sensor_readings=None,
            compromised_sensors=None
        )
        
        # Returns False because epd is None
        self.assertFalse(result)
    
    @patch('display.DISPLAY_AVAILABLE', True)
    def test_update_with_mock_display(self):
        """Test update with mocked display hardware"""
        mock_epd = MagicMock()
        
        with patch('display.epd2in13_V2.EPD', return_value=mock_epd):
            display = ThermostatDisplay()
            display.epd = mock_epd
            
            hvac_state = {'heat': True, 'cool': False, 'fan': True, 'heat2': False}
            
            result = display.update(
                system_temp=70.0,
                target_temp=68.0,
                hvac_state=hvac_state
            )
            
            # Should successfully update
            self.assertTrue(result)
            mock_epd.display.assert_called_once()
    
    @patch('display.DISPLAY_AVAILABLE', True)
    def test_clear_with_mock_display(self):
        """Test clear display"""
        mock_epd = MagicMock()
        
        with patch('display.epd2in13_V2.EPD', return_value=mock_epd):
            display = ThermostatDisplay()
            display.epd = mock_epd
            
            # Clear the call history from __init__
            mock_epd.Clear.reset_mock()
            
            display.clear()
            
            mock_epd.Clear.assert_called_once_with(0xFF)
    
    @patch('display.DISPLAY_AVAILABLE', True)
    def test_sleep_with_mock_display(self):
        """Test sleep display"""
        mock_epd = MagicMock()
        
        with patch('display.epd2in13_V2.EPD', return_value=mock_epd):
            display = ThermostatDisplay()
            display.epd = mock_epd
            
            display.sleep()
            
            mock_epd.sleep.assert_called_once()
    
    @patch('display.DISPLAY_AVAILABLE', True)
    def test_cleanup(self):
        """Test cleanup calls sleep"""
        mock_epd = MagicMock()
        
        with patch('display.epd2in13_V2.EPD', return_value=mock_epd):
            display = ThermostatDisplay()
            display.epd = mock_epd
            
            display.cleanup()
            
            mock_epd.sleep.assert_called_once()
    
    def test_update_handles_display_error(self):
        """Test update handles display errors gracefully"""
        mock_epd = MagicMock()
        mock_epd.display.side_effect = Exception("Display error")
        
        display = ThermostatDisplay()
        display.epd = mock_epd
        
        hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        
        # Should handle exception and return False
        result = display.update(
            system_temp=70.0,
            target_temp=68.0,
            hvac_state=hvac_state
        )
        
        self.assertFalse(result)


class TestDisplayDatabaseIntegration(unittest.TestCase):
    """Test display integration with database for temperature units"""
    
    def setUp(self):
        """Set up test with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Import here to avoid circular dependencies
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
        from database import ThermostatDatabase
        
        self.db = ThermostatDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_display_loads_temperature_units_from_database(self):
        """Test display loads temperature units from database"""
        # Save settings with Celsius
        self.db.save_settings(20.0, 25.0, 'heat', 'auto', 'C')
        
        # Create display with database
        display = ThermostatDisplay(database=self.db)
        
        # Create an image to trigger loading settings
        hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        display.create_display_image(20.0, 20.0, hvac_state, [], [])
        
        # Should load Celsius from database
        self.assertEqual(display.temperature_units, 'C')
    
    def test_display_handles_no_database_settings(self):
        """Test display handles missing database settings gracefully"""
        # Create new empty database
        display = ThermostatDisplay(database=self.db)
        
        # Should default to Fahrenheit
        self.assertEqual(display.temperature_units, 'F')


class TestDisplayExceptionHandling(unittest.TestCase):
    """Test display exception handling"""
    
    def test_clear_display_exception(self):
        """Test clear display handles exceptions"""
        mock_epd = MagicMock()
        mock_epd.Clear.side_effect = Exception("Clear error")
        
        display = ThermostatDisplay()
        display.epd = mock_epd
        
        # Should handle exception gracefully
        display.clear()
        # No assertion - just verifying no exception propagates
    
    def test_sleep_display_exception(self):
        """Test sleep display handles exceptions"""
        mock_epd = MagicMock()
        mock_epd.sleep.side_effect = Exception("Sleep error")
        
        display = ThermostatDisplay()
        display.epd = mock_epd
        
        # Should handle exception gracefully
        display.sleep()
        # No assertion - just verifying no exception propagates


if __name__ == '__main__':
    unittest.main()
