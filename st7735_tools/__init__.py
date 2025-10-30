"""
ST7735 Display Tools Package
Utilities for working with Arduino Due and ST7735 displays
"""

from .serial_utils import (
    get_native_usb_port,
    get_programming_port,
    get_preferred_port,
    find_arduino_due_ports,
    print_arduino_due_info,
    list_all_ports,
    ArduinoDuePort
)

__version__ = "1.0.0"
__all__ = [
    'get_native_usb_port',
    'get_programming_port',
    'get_preferred_port',
    'find_arduino_due_ports',
    'print_arduino_due_info',
    'list_all_ports',
    'ArduinoDuePort'
]
