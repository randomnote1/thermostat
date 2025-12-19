#!/usr/bin/env python3
"""
Test script for relay board
"""

import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Error: RPi.GPIO library not installed")
    print("This script must run on a Raspberry Pi")
    sys.exit(1)


# GPIO pin assignments (BCM numbering)
RELAY_HEAT = 17
RELAY_COOL = 27
RELAY_FAN = 22
RELAY_HEAT2 = 23

RELAYS = {
    'Heat': RELAY_HEAT,
    'Cool': RELAY_COOL,
    'Fan': RELAY_FAN,
    'Heat2': RELAY_HEAT2
}


def setup_gpio():
    """Initialize GPIO"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    for name, pin in RELAYS.items():
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        print(f"Configured GPIO {pin} ({name}) as output")


def test_relay(name, pin, duration=2):
    """Test a single relay"""
    print(f"\nTesting {name} relay (GPIO {pin})...")
    print(f"  Turning ON for {duration} seconds...")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duration)
    
    print(f"  Turning OFF...")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(1)


def test_all_relays():
    """Test all relays sequentially"""
    print("=" * 60)
    print("Relay Board Test")
    print("=" * 60)
    print()
    print("Watch/listen for relay clicks and LED indicators")
    print()
    
    setup_gpio()
    
    try:
        # Test each relay individually
        for name, pin in RELAYS.items():
            test_relay(name, pin)
        
        # Test all together
        print("\n" + "=" * 60)
        print("Testing all relays together...")
        print("=" * 60)
        print("\nTurning ALL relays ON for 3 seconds...")
        for pin in RELAYS.values():
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(3)
        
        print("Turning ALL relays OFF...")
        for pin in RELAYS.values():
            GPIO.output(pin, GPIO.LOW)
        
        print("\n" + "=" * 60)
        print("Test complete!")
        print("=" * 60)
        print("\nVerify:")
        print("- Each relay clicked when activated")
        print("- LEDs on relay board lit up")
        print("- No unexpected behavior")
        print()
        print("⚠️  WARNING: Do NOT connect to HVAC system yet!")
        print("   Connect a multimeter to verify relay switching first")
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted!")
    
    finally:
        # Clean up
        print("\nCleaning up GPIO...")
        for pin in RELAYS.values():
            GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup()
        print("Done!")


def interactive_test():
    """Interactive relay testing"""
    print("=" * 60)
    print("Interactive Relay Test")
    print("=" * 60)
    print()
    
    setup_gpio()
    
    try:
        while True:
            print("\nCommands:")
            print("  1 - Toggle Heat relay")
            print("  2 - Toggle Cool relay")
            print("  3 - Toggle Fan relay")
            print("  4 - Toggle Heat2 relay")
            print("  0 - Turn all OFF")
            print("  q - Quit")
            print()
            
            choice = input("Enter command: ").strip()
            
            if choice == 'q':
                break
            elif choice == '0':
                for pin in RELAYS.values():
                    GPIO.output(pin, GPIO.LOW)
                print("All relays OFF")
            elif choice in ['1', '2', '3', '4']:
                relay_name = list(RELAYS.keys())[int(choice) - 1]
                relay_pin = list(RELAYS.values())[int(choice) - 1]
                
                current_state = GPIO.input(relay_pin)
                new_state = not current_state
                GPIO.output(relay_pin, GPIO.HIGH if new_state else GPIO.LOW)
                
                print(f"{relay_name} relay: {'ON' if new_state else 'OFF'}")
            else:
                print("Invalid command")
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    
    finally:
        print("\nCleaning up GPIO...")
        for pin in RELAYS.values():
            GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup()
        print("Done!")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_test()
    else:
        test_all_relays()
        print("\nRun with --interactive flag for manual control")


if __name__ == '__main__':
    main()
