#!/usr/bin/env python3
"""
E-Ink Display Module for Thermostat
Handles updating the Waveshare e-ink display
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

try:
    from waveshare_epd import epd2in13_V2
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Warning: Waveshare EPD library not available")


class ThermostatDisplay:
    """Manages the e-ink display for the thermostat"""
    
    def __init__(self):
        self.display_type = os.getenv('DISPLAY_TYPE', 'waveshare_2in13_v2')
        self.width = 250
        self.height = 122
        self.epd = None
        
        if DISPLAY_AVAILABLE:
            try:
                self.epd = epd2in13_V2.EPD()
                self.epd.init(self.epd.FULL_UPDATE)
                self.epd.Clear(0xFF)
                print("E-ink display initialized")
            except Exception as e:
                print(f"Warning: Could not initialize display: {e}")
                self.epd = None
        
        # Load fonts
        try:
            self.font_large = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
            self.font_medium = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
            self.font_small = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
            self.font_tiny = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
        except:
            # Fall back to default font
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()
    
    def create_display_image(self, system_temp: float, target_temp: float, 
                            hvac_state: Dict, sensor_readings: List,
                            compromised_sensors: List[str]) -> Image:
        """Create an image for the display"""
        # Create blank image (note: rotated 90 degrees for landscape)
        image = Image.new('1', (self.height, self.width), 255)
        draw = ImageDraw.Draw(image)
        
        # Current temperature (large, centered top)
        temp_str = f"{system_temp:.1f}"
        draw.text((10, 5), temp_str, font=self.font_large, fill=0)
        draw.text((90, 20), "°F", font=self.font_small, fill=0)
        
        # Target temperature
        target_str = f"Target: {target_temp:.1f}°F"
        draw.text((10, 45), target_str, font=self.font_small, fill=0)
        
        # HVAC status
        status_parts = []
        if hvac_state.get('heat'): status_parts.append("HEAT")
        if hvac_state.get('cool'): status_parts.append("COOL")
        if hvac_state.get('fan'): status_parts.append("FAN")
        if hvac_state.get('heat2'): status_parts.append("HEAT2")
        
        status_str = "+".join(status_parts) if status_parts else "OFF"
        draw.text((10, 60), f"HVAC: {status_str}", font=self.font_medium, fill=0)
        
        # Divider line
        draw.line([(10, 85), (self.height-10, 85)], fill=0, width=1)
        
        # Individual sensor readings (small, scrolling if needed)
        y_pos = 90
        for reading in sensor_readings[:5]:  # Show up to 5 sensors
            sensor_name = reading.name[:10]  # Truncate long names
            temp = reading.temperature
            
            # Mark compromised sensors
            marker = "!" if reading.sensor_id in compromised_sensors else " "
            
            text = f"{marker}{sensor_name}: {temp:.1f}°F"
            draw.text((10, y_pos), text, font=self.font_tiny, fill=0)
            y_pos += 12
        
        # Timestamp
        time_str = datetime.now().strftime("%m/%d %H:%M")
        draw.text((self.height-60, 235), time_str, font=self.font_tiny, fill=0)
        
        return image
    
    def update(self, system_temp: float, target_temp: float, 
              hvac_state: Dict, sensor_readings: List = None,
              compromised_sensors: List[str] = None) -> bool:
        """Update the display with current information"""
        if not self.epd:
            # No display available, skip
            return False
        
        if sensor_readings is None:
            sensor_readings = []
        if compromised_sensors is None:
            compromised_sensors = []
        
        try:
            # Create image
            image = self.create_display_image(
                system_temp, target_temp, hvac_state, 
                sensor_readings, compromised_sensors
            )
            
            # Update display
            self.epd.display(self.epd.getbuffer(image))
            return True
        
        except Exception as e:
            print(f"Error updating display: {e}")
            return False
    
    def clear(self):
        """Clear the display"""
        if self.epd:
            try:
                self.epd.Clear(0xFF)
            except Exception as e:
                print(f"Error clearing display: {e}")
    
    def sleep(self):
        """Put display in low-power sleep mode"""
        if self.epd:
            try:
                self.epd.sleep()
            except Exception as e:
                print(f"Error sleeping display: {e}")
    
    def cleanup(self):
        """Clean up display resources"""
        self.sleep()
