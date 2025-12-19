#!/usr/bin/env python3
"""
Test script for e-ink display
Creates a simple test pattern on the Waveshare e-ink display
"""

import sys
import time
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow library not installed")
    print("Install with: pip install Pillow")
    sys.exit(1)

# Try to import display library
try:
    # For Waveshare 2.13" v2
    from waveshare_epd import epd2in13_V2
    display_available = True
except ImportError:
    print("Warning: Waveshare EPD library not installed")
    print("Install with: pip install waveshare-epaper")
    print("\nRunning in simulation mode - image will be saved to file")
    display_available = False


def create_test_image(width, height):
    """Create a test image for the display"""
    # Create blank image
    image = Image.new('1', (width, height), 255)  # 1-bit color, white background
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if unavailable
    try:
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    except:
        print("Using default font (TrueType fonts not found)")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw border
    draw.rectangle([(0, 0), (width-1, height-1)], outline=0)
    
    # Draw title
    draw.text((10, 10), "Thermostat Test", font=font_large, fill=0)
    
    # Draw current time
    current_time = datetime.now().strftime("%H:%M:%S")
    draw.text((10, 40), f"Time: {current_time}", font=font_medium, fill=0)
    
    # Draw temperature display area
    draw.text((10, 65), "Temp: 72.5°F", font=font_medium, fill=0)
    draw.text((10, 85), "Target: 68.0°F", font=font_small, fill=0)
    draw.text((10, 100), "HVAC: HEAT", font=font_small, fill=0)
    
    return image


def test_display_waveshare():
    """Test Waveshare e-ink display"""
    print("=" * 60)
    print("Waveshare E-Ink Display Test")
    print("=" * 60)
    print()
    
    try:
        # Initialize display
        print("Initializing display...")
        epd = epd2in13_V2.EPD()
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)
        
        print(f"Display size: {epd.width}x{epd.height}")
        print()
        
        # Create test image
        print("Creating test image...")
        image = create_test_image(epd.height, epd.width)  # Note: rotated 90 degrees
        
        # Display image
        print("Displaying image (this may take 10-15 seconds)...")
        epd.display(epd.getbuffer(image))
        
        print("\n✓ Test image displayed successfully!")
        print("\nThe display should show:")
        print("  - Border around the edge")
        print("  - Title 'Thermostat Test'")
        print("  - Current time")
        print("  - Sample temperature readings")
        print()
        
        # Sleep display
        print("Putting display to sleep...")
        epd.sleep()
        
        print("\n" + "=" * 60)
        print("Test complete!")
        print("=" * 60)
    
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("- Check if SPI is enabled: ls /dev/spi*")
        print("- Verify display HAT is properly seated on GPIO pins")
        print("- Try: sudo raspi-config → Interface Options → SPI → Enable")


def simulate_display():
    """Simulate display by saving image to file"""
    print("=" * 60)
    print("E-Ink Display Simulation")
    print("=" * 60)
    print()
    
    width, height = 250, 122  # Waveshare 2.13" dimensions
    
    print(f"Creating test image ({width}x{height})...")
    image = create_test_image(width, height)
    
    filename = "display_test.png"
    image.save(filename)
    
    print(f"✓ Test image saved to: {filename}")
    print("\nOpen this file to preview what will appear on the e-ink display")


def main():
    if display_available:
        test_display_waveshare()
    else:
        simulate_display()


if __name__ == '__main__':
    main()
