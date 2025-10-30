#!/usr/bin/env python3
"""
Test script to demonstrate st7735_tools Arduino Due port detection
"""

from st7735_tools import (
    get_native_usb_port,
    get_programming_port,
    get_preferred_port,
    find_arduino_due_ports,
    print_arduino_due_info
)

print("=== ST7735 Tools - Port Detection Test ===\n")

# Test 1: Individual port getters
print("1. Individual Port Detection:")
native = get_native_usb_port()
programming = get_programming_port()
print(f"   Native USB port: {native}")
print(f"   Programming port: {programming}")
print()

# Test 2: Preferred port with fallback
print("2. Preferred Port Detection:")
print(f"   Prefer Native USB: {get_preferred_port(prefer_native=True)}")
print(f"   Prefer Programming: {get_preferred_port(prefer_native=False)}")
print()

# Test 3: Detailed port information
print("3. Detailed Port Information:")
ports = find_arduino_due_ports()
if ports['native']:
    print(f"   Native USB:")
    print(f"     Device: {ports['native'].device}")
    print(f"     Description: {ports['native'].description}")
    print(f"     VID:PID: {ports['native'].vid:04X}:{ports['native'].pid:04X}")
if ports['programming']:
    print(f"   Programming Port:")
    print(f"     Device: {ports['programming'].device}")
    print(f"     Description: {ports['programming'].description}")
    print(f"     VID:PID: {ports['programming'].vid:04X}:{ports['programming'].pid:04X}")
print()

# Test 4: Formatted detection info with return values
print("4. Formatted Detection with Return Values:")
detected_ports = print_arduino_due_info()
print(f"   Returned values:")
print(f"     native: {detected_ports['native']}")
print(f"     programming: {detected_ports['programming']}")
