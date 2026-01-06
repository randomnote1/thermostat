#!/usr/bin/env python3
"""
Unit tests for temperature_utils module
"""

import unittest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from temperature_utils import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    celsius_to_kelvin,
    kelvin_to_celsius,
    fahrenheit_to_kelvin,
    kelvin_to_fahrenheit,
    convert_temperature,
    get_unit_symbol,
    format_temperature
)


class TestTemperatureConversion(unittest.TestCase):
    """Test temperature conversion functions"""
    
    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion"""
        self.assertAlmostEqual(celsius_to_fahrenheit(0), 32.0, places=1)
        self.assertAlmostEqual(celsius_to_fahrenheit(100), 212.0, places=1)
        self.assertAlmostEqual(celsius_to_fahrenheit(20), 68.0, places=1)
        self.assertAlmostEqual(celsius_to_fahrenheit(-40), -40.0, places=1)
        self.assertAlmostEqual(celsius_to_fahrenheit(37), 98.6, places=1)
    
    def test_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion"""
        self.assertAlmostEqual(fahrenheit_to_celsius(32), 0.0, places=1)
        self.assertAlmostEqual(fahrenheit_to_celsius(212), 100.0, places=1)
        self.assertAlmostEqual(fahrenheit_to_celsius(68), 20.0, places=1)
        self.assertAlmostEqual(fahrenheit_to_celsius(-40), -40.0, places=1)
        self.assertAlmostEqual(fahrenheit_to_celsius(98.6), 37.0, places=1)
    
    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion"""
        self.assertAlmostEqual(celsius_to_kelvin(0), 273.15, places=2)
        self.assertAlmostEqual(celsius_to_kelvin(100), 373.15, places=2)
        self.assertAlmostEqual(celsius_to_kelvin(-273.15), 0, places=2)
    
    def test_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion"""
        self.assertAlmostEqual(kelvin_to_celsius(273.15), 0, places=2)
        self.assertAlmostEqual(kelvin_to_celsius(373.15), 100, places=2)
        self.assertAlmostEqual(kelvin_to_celsius(0), -273.15, places=2)
    
    def test_fahrenheit_to_kelvin(self):
        """Test Fahrenheit to Kelvin conversion"""
        self.assertAlmostEqual(fahrenheit_to_kelvin(32), 273.15, places=2)
        self.assertAlmostEqual(fahrenheit_to_kelvin(212), 373.15, places=2)
    
    def test_kelvin_to_fahrenheit(self):
        """Test Kelvin to Fahrenheit conversion"""
        self.assertAlmostEqual(kelvin_to_fahrenheit(273.15), 32, places=1)
        self.assertAlmostEqual(kelvin_to_fahrenheit(373.15), 212, places=1)
    
    def test_round_trip_conversion(self):
        """Test converting back and forth preserves value"""
        original_c = 22.5
        fahrenheit = celsius_to_fahrenheit(original_c)
        back_to_c = fahrenheit_to_celsius(fahrenheit)
        self.assertAlmostEqual(original_c, back_to_c, places=2)
        
        original_f = 72.5
        celsius = fahrenheit_to_celsius(original_f)
        back_to_f = celsius_to_fahrenheit(celsius)
        self.assertAlmostEqual(original_f, back_to_f, places=2)


class TestUniversalConversion(unittest.TestCase):
    """Test universal temperature conversion function"""
    
    def test_convert_temperature_same_unit(self):
        """Test conversion with same source and target unit"""
        self.assertEqual(convert_temperature(25, 'C', 'C'), 25)
        self.assertEqual(convert_temperature(77, 'F', 'F'), 77)
        self.assertEqual(convert_temperature(298, 'K', 'K'), 298)
    
    def test_convert_temperature_all_combinations(self):
        """Test conversion between all unit combinations"""
        # C to F
        self.assertAlmostEqual(convert_temperature(20, 'C', 'F'), 68.0, places=1)
        # F to C
        self.assertAlmostEqual(convert_temperature(68, 'F', 'C'), 20.0, places=1)
        # C to K
        self.assertAlmostEqual(convert_temperature(20, 'C', 'K'), 293.15, places=2)
        # K to C
        self.assertAlmostEqual(convert_temperature(293.15, 'K', 'C'), 20, places=1)
        # F to K
        self.assertAlmostEqual(convert_temperature(68, 'F', 'K'), 293.15, places=2)
        # K to F
        self.assertAlmostEqual(convert_temperature(293.15, 'K', 'F'), 68, places=1)
    
    def test_convert_temperature_case_insensitive(self):
        """Test that units are case-insensitive"""
        result1 = convert_temperature(20, 'c', 'f')
        result2 = convert_temperature(20, 'C', 'F')
        self.assertAlmostEqual(result1, result2, places=2)
    
    def test_convert_temperature_invalid_source(self):
        """Test error handling for invalid source unit"""
        with self.assertRaises(ValueError) as cm:
            convert_temperature(20, 'X', 'F')
        self.assertIn('Unsupported', str(cm.exception))
    
    def test_convert_temperature_invalid_target(self):
        """Test error handling for invalid target unit"""
        with self.assertRaises(ValueError) as cm:
            convert_temperature(20, 'C', 'X')
        self.assertIn('Unsupported', str(cm.exception))


class TestFormatting(unittest.TestCase):
    """Test temperature formatting functions"""
    
    def test_get_unit_symbol(self):
        """Test getting unit symbols"""
        self.assertEqual(get_unit_symbol('F'), '°F')
        self.assertEqual(get_unit_symbol('C'), '°C')
        self.assertEqual(get_unit_symbol('K'), 'K')
        self.assertEqual(get_unit_symbol('f'), '°F')  # Case insensitive
        self.assertEqual(get_unit_symbol('c'), '°C')
        self.assertEqual(get_unit_symbol('X'), '°F')  # Default fallback
    
    def test_format_temperature(self):
        """Test formatting temperature with symbol"""
        self.assertEqual(format_temperature(72.5, 'F'), '72.5°F')
        self.assertEqual(format_temperature(20.0, 'C'), '20.0°C')
        self.assertEqual(format_temperature(293.15, 'K'), '293.1K')
    
    def test_format_temperature_precision(self):
        """Test formatting with different precision"""
        self.assertEqual(format_temperature(72.567, 'F', precision=0), '73°F')
        self.assertEqual(format_temperature(72.567, 'F', precision=1), '72.6°F')
        self.assertEqual(format_temperature(72.567, 'F', precision=2), '72.57°F')


if __name__ == '__main__':
    unittest.main()
