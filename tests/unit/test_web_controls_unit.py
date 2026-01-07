#!/usr/bin/env python3
"""
Unit tests for web interface control functionality
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


@pytest.fixture
def mock_controller():
    """Create a mock ThermostatController for testing controls"""
    # Add src to path
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    
    with patch('thermostat.GPIO', None), \
         patch('thermostat.W1ThermSensor', None):
        import os
        from unittest.mock import patch as env_patch
        
        # Mock environment with database disabled
        with env_patch.dict(os.environ, {
            'DATABASE_PATH': '',  # No database
            'LOG_LEVEL': 'ERROR',
            'TARGET_TEMP_HEAT': '68.0',
            'TARGET_TEMP_COOL': '74.0',
            'GPIO_RELAY_HEAT': '17',
            'GPIO_RELAY_COOL': '27',
            'GPIO_RELAY_FAN': '22',
            'GPIO_RELAY_HEAT2': '23',
        }):
            from thermostat import ThermostatController
            
            controller = ThermostatController()
            controller.target_temp_heat = 20.0  # 68°F in Celsius
            controller.target_temp_cool = 23.33  # 74°F in Celsius
            controller.hvac_mode = 'heat'
            
            yield controller


class TestTemperatureControl:
    """Test temperature setpoint controls"""
    
    def test_set_heat_temperature_valid(self, mock_controller):
        """Test setting heating temperature within valid range"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'heat',
            'temperature': 21.0  # Celsius
        })
        
        assert result['success'] is True
        assert mock_controller.target_temp_heat == 21.0
        assert 'Target heat temperature set to 21.0°C' in result['message']
    
    def test_set_cool_temperature_valid(self, mock_controller):
        """Test setting cooling temperature within valid range"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'cool',
            'temperature': 22.0  # Celsius
        })
        
        assert result['success'] is True
        assert mock_controller.target_temp_cool == 22.0
        assert 'Target cool temperature set to 22.0°C' in result['message']
    
    def test_set_temperature_too_low(self, mock_controller):
        """Test temperature below minimum (10°C) is rejected"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'heat',
            'temperature': 5.0  # Below 10°C minimum
        })
        
        assert result['success'] is False
        assert 'out of range' in result['error'].lower()
        assert mock_controller.target_temp_heat == 20.0  # Unchanged
    
    def test_set_temperature_too_high(self, mock_controller):
        """Test temperature above maximum (32°C) is rejected"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'cool',
            'temperature': 40.0  # Above 32°C maximum
        })
        
        assert result['success'] is False
        assert 'out of range' in result['error'].lower()
        assert mock_controller.target_temp_cool == 23.33  # Unchanged
    
    def test_set_temperature_invalid_type(self, mock_controller):
        """Test invalid temperature type is rejected"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'invalid',
            'temperature': 21.0  # Celsius
        })
        
        assert result['success'] is False
        assert 'Invalid temperature type' in result['error'] or 'out of range' in result['error'].lower()


class TestModeControl:
    """Test HVAC mode control"""
    
    def test_set_mode_heat(self, mock_controller):
        """Test setting mode to heat"""
        result = mock_controller.handle_control_command('set_mode', {
            'mode': 'heat'
        })
        
        assert result['success'] is True
        assert mock_controller.hvac_mode == 'heat'
    
    def test_set_mode_cool(self, mock_controller):
        """Test setting mode to cool"""
        result = mock_controller.handle_control_command('set_mode', {
            'mode': 'cool'
        })
        
        assert result['success'] is True
        assert mock_controller.hvac_mode == 'cool'
    
    def test_set_mode_auto(self, mock_controller):
        """Test setting mode to auto"""
        result = mock_controller.handle_control_command('set_mode', {
            'mode': 'auto'
        })
        
        assert result['success'] is True
        assert mock_controller.hvac_mode == 'auto'
    
    def test_set_mode_off(self, mock_controller):
        """Test setting mode to off"""
        # First set some HVAC state
        mock_controller.hvac_state = {
            'heat': True,
            'cool': False,
            'fan': True,
            'heat2': False
        }
        
        result = mock_controller.handle_control_command('set_mode', {
            'mode': 'off'
        })
        
        assert result['success'] is True
        assert mock_controller.hvac_mode == 'off'
        # Verify HVAC is turned off
        assert mock_controller.hvac_state['heat'] is False
        assert mock_controller.hvac_state['cool'] is False
        assert mock_controller.hvac_state['fan'] is False
    
    def test_set_mode_invalid(self, mock_controller):
        """Test invalid mode is rejected"""
        original_mode = mock_controller.hvac_mode
        
        result = mock_controller.handle_control_command('set_mode', {
            'mode': 'invalid_mode'
        })
        
        assert result['success'] is False
        assert 'Invalid mode' in result['error']
        assert mock_controller.hvac_mode == original_mode  # Unchanged


class TestFanControl:
    """Test manual fan control"""
    
    def test_set_fan_on(self, mock_controller):
        """Test turning fan on"""
        result = mock_controller.handle_control_command('set_fan', {
            'fan_on': True
        })
        
        assert result['success'] is True
        assert mock_controller.hvac_state['fan'] is True
        assert mock_controller.manual_fan_mode is True
        assert 'CONTINUOUS' in result['message']
    
    def test_set_fan_off(self, mock_controller):
        """Test turning fan off"""
        mock_controller.hvac_state['fan'] = True
        
        result = mock_controller.handle_control_command('set_fan', {
            'fan_on': False
        })
        
        assert result['success'] is True
        assert mock_controller.hvac_state['fan'] is False
        assert mock_controller.manual_fan_mode is True
        assert 'AUTO' in result['message']


class TestControlValidation:
    """Test control command validation and error handling"""
    
    def test_unknown_command(self, mock_controller):
        """Test unknown command is rejected"""
        result = mock_controller.handle_control_command('invalid_command', {})
        
        assert result['success'] is False
        assert 'Unknown command' in result['error']
    
    def test_temperature_boundary_minimum(self, mock_controller):
        """Test minimum temperature boundary (10°C)"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'heat',
            'temperature': 10.0  # Celsius minimum
        })
        
        assert result['success'] is True
        assert mock_controller.target_temp_heat == 10.0
    
    def test_temperature_boundary_maximum(self, mock_controller):
        """Test maximum temperature boundary (32°C)"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'cool',
            'temperature': 32.0  # Celsius maximum
        })
        
        assert result['success'] is True
        assert mock_controller.target_temp_cool == 32.0
    
    def test_temperature_just_below_minimum(self, mock_controller):
        """Test temperature just below minimum is rejected"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'heat',
            'temperature': 49.9
        })
        
        assert result['success'] is False
    
    def test_temperature_just_above_maximum(self, mock_controller):
        """Test temperature just above maximum is rejected"""
        result = mock_controller.handle_control_command('set_temperature', {
            'type': 'cool',
            'temperature': 90.1
        })
        
        assert result['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
