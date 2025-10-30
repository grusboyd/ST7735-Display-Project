#!/usr/bin/env python3
"""
Example: Using st7735_tools package in your own scripts
"""

from st7735_tools import (
    get_native_usb_port,
    get_programming_port,
    find_arduino_due_ports,
    print_arduino_due_info
)
import serial

def example_1_simple_detection():
    """Example 1: Simple auto-detection"""
    print("=== Example 1: Simple Auto-Detection ===")
    
    port = get_native_usb_port()
    if port:
        print(f"✓ Native USB port: {port}")
    else:
        print("✗ Native USB port not found")
    print()

def example_2_detailed_info():
    """Example 2: Get detailed port information"""
    print("=== Example 2: Detailed Port Info ===")
    
    ports = find_arduino_due_ports()
    
    if ports['native']:
        print(f"Native USB:")
        print(f"  Device: {ports['native'].device}")
        print(f"  Description: {ports['native'].description}")
        print(f"  VID:PID: {ports['native'].vid:04X}:{ports['native'].pid:04X}")
    
    if ports['programming']:
        print(f"Programming Port:")
        print(f"  Device: {ports['programming'].device}")
        print(f"  Description: {ports['programming'].description}")
        print(f"  VID:PID: {ports['programming'].vid:04X}:{ports['programming'].pid:04X}")
    print()

def example_3_connect_and_communicate():
    """Example 3: Connect and send a test message"""
    print("=== Example 3: Connect and Communicate ===")
    
    port = get_native_usb_port()
    if not port:
        print("✗ Cannot proceed - no Native USB port found")
        return
    
    try:
        print(f"Connecting to {port}...")
        ser = serial.Serial(port, 115200, timeout=2)
        
        # Wait for Arduino to initialize
        import time
        time.sleep(2)
        
        # Read any startup messages
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"Arduino: {line}")
        
        print("✓ Connection successful!")
        ser.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
    print()

if __name__ == "__main__":
    print("ST7735 Tools Package - Usage Examples\n")
    
    # Run examples
    example_1_simple_detection()
    example_2_detailed_info()
    
    # Show formatted detection info
    print("=== Full Detection Info ===")
    print_arduino_due_info()
    print()
    
    # Uncomment to test actual communication
    # example_3_connect_and_communicate()
