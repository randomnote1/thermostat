#!/usr/bin/env python3
"""
Temperature conversion utilities for thermostat
Handles conversion between Celsius, Fahrenheit, and Kelvin
"""

from typing import Union


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit
    
    Args:
        celsius: Temperature in degrees Celsius
        
    Returns:
        Temperature in degrees Fahrenheit
    """
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius
    
    Args:
        fahrenheit: Temperature in degrees Fahrenheit
        
    Returns:
        Temperature in degrees Celsius
    """
    return (fahrenheit - 32) * 5/9


def celsius_to_kelvin(celsius: float) -> float:
    """Convert Celsius to Kelvin
    
    Args:
        celsius: Temperature in degrees Celsius
        
    Returns:
        Temperature in Kelvin
    """
    return celsius + 273.15


def kelvin_to_celsius(kelvin: float) -> float:
    """Convert Kelvin to Celsius
    
    Args:
        kelvin: Temperature in Kelvin
        
    Returns:
        Temperature in degrees Celsius
    """
    return kelvin - 273.15


def fahrenheit_to_kelvin(fahrenheit: float) -> float:
    """Convert Fahrenheit to Kelvin
    
    Args:
        fahrenheit: Temperature in degrees Fahrenheit
        
    Returns:
        Temperature in Kelvin
    """
    return celsius_to_kelvin(fahrenheit_to_celsius(fahrenheit))


def kelvin_to_fahrenheit(kelvin: float) -> float:
    """Convert Kelvin to Fahrenheit
    
    Args:
        kelvin: Temperature in Kelvin
        
    Returns:
        Temperature in degrees Fahrenheit
    """
    return celsius_to_fahrenheit(kelvin_to_celsius(kelvin))


def convert_temperature(temp: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between any supported units
    
    Args:
        temp: Temperature value to convert
        from_unit: Source unit ('C', 'F', or 'K')
        to_unit: Target unit ('C', 'F', or 'K')
        
    Returns:
        Converted temperature value
        
    Raises:
        ValueError: If unit is not supported
    """
    # Normalize units to uppercase
    from_unit = from_unit.upper()
    to_unit = to_unit.upper()
    
    # No conversion needed
    if from_unit == to_unit:
        return temp
    
    # Convert to Celsius first (our base unit)
    if from_unit == 'C':
        temp_celsius = temp
    elif from_unit == 'F':
        temp_celsius = fahrenheit_to_celsius(temp)
    elif from_unit == 'K':
        temp_celsius = kelvin_to_celsius(temp)
    else:
        raise ValueError(f"Unsupported temperature unit: {from_unit}")
    
    # Convert from Celsius to target unit
    if to_unit == 'C':
        return temp_celsius
    elif to_unit == 'F':
        return celsius_to_fahrenheit(temp_celsius)
    elif to_unit == 'K':
        return celsius_to_kelvin(temp_celsius)
    else:
        raise ValueError(f"Unsupported temperature unit: {to_unit}")


def get_unit_symbol(unit: str) -> str:
    """Get the display symbol for a temperature unit
    
    Args:
        unit: Temperature unit ('C', 'F', or 'K')
        
    Returns:
        Display symbol (e.g., '°F', '°C', 'K')
    """
    unit = unit.upper()
    if unit == 'F':
        return '°F'
    elif unit == 'C':
        return '°C'
    elif unit == 'K':
        return 'K'
    else:
        return '°F'  # Default fallback


def format_temperature(temp: float, unit: str, precision: int = 1) -> str:
    """Format temperature value with unit symbol
    
    Args:
        temp: Temperature value
        unit: Temperature unit ('C', 'F', or 'K')
        precision: Number of decimal places (default 1)
        
    Returns:
        Formatted temperature string (e.g., "72.5°F")
    """
    symbol = get_unit_symbol(unit)
    return f"{temp:.{precision}f}{symbol}"
