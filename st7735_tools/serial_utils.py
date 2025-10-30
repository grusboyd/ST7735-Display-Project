#!/usr/bin/env python3
"""
Serial Utilities for Arduino Due
Detects and identifies Arduino Due serial ports (Programming and Native USB)
"""

import serial.tools.list_ports
from typing import Optional, Dict, List

class ArduinoDuePort:
    """Represents an Arduino Due serial port"""
    def __init__(self, device: str, description: str, is_native: bool, vid: int, pid: int):
        self.device = device
        self.description = description
        self.is_native = is_native
        self.vid = vid
        self.pid = pid
    
    def __str__(self):
        port_type = "Native USB" if self.is_native else "Programming Port"
        return f"{self.device} - {self.description} ({port_type})"
    
    def __repr__(self):
        return f"ArduinoDuePort(device='{self.device}', is_native={self.is_native})"

def find_arduino_due_ports() -> Dict[str, Optional[ArduinoDuePort]]:
    """
    Find Arduino Due serial ports
    
    Returns:
        dict: Dictionary with keys 'native' and 'programming', values are ArduinoDuePort or None
        
    Example:
        ports = find_arduino_due_ports()
        if ports['native']:
            print(f"Native port: {ports['native'].device}")
    """
    # Arduino Due USB VID:PID identifiers
    # Programming Port: VID=2A03, PID=003D (or VID=2341, PID=003D)
    # Native USB Port: VID=2341, PID=003E
    
    PROGRAMMING_PIDS = [0x003D]  # Programming port
    NATIVE_PID = 0x003E           # Native USB port
    ARDUINO_VIDS = [0x2A03, 0x2341]  # Arduino VIDs
    
    result = {
        'native': None,
        'programming': None
    }
    
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        # Check if it's an Arduino Due
        if port.vid in ARDUINO_VIDS:
            if port.pid == NATIVE_PID:
                result['native'] = ArduinoDuePort(
                    device=port.device,
                    description=port.description,
                    is_native=True,
                    vid=port.vid,
                    pid=port.pid
                )
            elif port.pid in PROGRAMMING_PIDS:
                result['programming'] = ArduinoDuePort(
                    device=port.device,
                    description=port.description,
                    is_native=False,
                    vid=port.vid,
                    pid=port.pid
                )
    
    return result

def get_native_usb_port() -> Optional[str]:
    """
    Get the Arduino Due Native USB port device path
    
    Returns:
        str: Device path (e.g., '/dev/ttyACM1') or None if not found
        
    Example:
        port = get_native_usb_port()
        if port:
            ser = serial.Serial(port, 115200)
    """
    ports = find_arduino_due_ports()
    if ports['native']:
        return ports['native'].device
    return None

def get_programming_port() -> Optional[str]:
    """
    Get the Arduino Due Programming Port device path
    
    Returns:
        str: Device path (e.g., '/dev/ttyACM0') or None if not found
    """
    ports = find_arduino_due_ports()
    if ports['programming']:
        return ports['programming'].device
    return None

def get_preferred_port(prefer_native: bool = True) -> Optional[str]:
    """
    Get preferred Arduino Due port with fallback
    
    Args:
        prefer_native (bool): If True, prefer Native USB over Programming port. 
                             If False, prefer Programming port over Native USB.
    
    Returns:
        str: Device path or None if no Arduino Due found
        
    Example:
        # Get Native USB if available, fallback to Programming port
        port = get_preferred_port(prefer_native=True)
        
        # Get Programming port if available, fallback to Native USB
        port = get_preferred_port(prefer_native=False)
    """
    ports = find_arduino_due_ports()
    
    if prefer_native:
        # Prefer Native USB, fallback to Programming
        if ports['native']:
            return ports['native'].device
        elif ports['programming']:
            return ports['programming'].device
    else:
        # Prefer Programming, fallback to Native USB
        if ports['programming']:
            return ports['programming'].device
        elif ports['native']:
            return ports['native'].device
    
    return None

def list_all_ports() -> List[Dict[str, str]]:
    """
    List all available serial ports
    
    Returns:
        list: List of dictionaries with 'device', 'description', and 'hwid' keys
    """
    ports = serial.tools.list_ports.comports()
    return [
        {
            'device': port.device,
            'description': port.description,
            'hwid': port.hwid
        }
        for port in ports
    ]

def print_arduino_due_info(show_ports: bool = True):
    """
    Print information about connected Arduino Due boards
    
    Args:
        show_ports (bool): If True, display port paths in output
        
    Returns:
        dict: Dictionary with 'native' and 'programming' port paths (or None)
    """
    ports = find_arduino_due_ports()
    
    print("=== Arduino Due Port Detection ===")
    
    result = {'native': None, 'programming': None}
    
    if ports['native']:
        result['native'] = ports['native'].device
        if show_ports:
            print(f"✓ Native USB Port found: {ports['native']}")
            print(f"  → Use this port for SerialUSB communication (no resets)")
        else:
            print(f"✓ Native USB Port found: {ports['native'].description}")
    else:
        print("✗ Native USB Port not found")
    
    if ports['programming']:
        result['programming'] = ports['programming'].device
        if show_ports:
            print(f"✓ Programming Port found: {ports['programming']}")
            print(f"  → Use this port for uploading code (resets on connection)")
        else:
            print(f"✓ Programming Port found: {ports['programming'].description}")
    else:
        print("✗ Programming Port not found")
    
    if not ports['native'] and not ports['programming']:
        print("\nNo Arduino Due boards detected!")
        print("Available serial ports:")
        for port_info in list_all_ports():
            print(f"  {port_info['device']} - {port_info['description']}")
    
    return result

if __name__ == "__main__":
    # Test/demo mode
    print_arduino_due_info()
