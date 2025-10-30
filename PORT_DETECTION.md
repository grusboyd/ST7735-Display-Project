# ST7735 Tools - Arduino Due Port Detection

## Overview
The `st7735_tools` package provides automatic detection of Arduino Due serial ports with support for both Native USB and Programming ports.

## Key Features

### Functions Added:
- `get_native_usb_port()` - Returns Native USB port path or None
- `get_programming_port()` - Returns Programming port path or None  
- `get_preferred_port(prefer_native=True)` - Smart port selection with fallback
- `print_arduino_due_info()` - Display detection info and return port paths

### New bitmap_sender.py Options:
- `--use-programming-port` - Force use of Programming port
- `--detect-arduino` - Show detected ports
- Auto-detection by default (prefers Native USB)

## Usage Examples

### Command Line:
```bash
# Auto-detect Native USB (default, recommended)
python3 bitmap_sender.py tiger.png

# Use Programming port (will cause reset)
python3 bitmap_sender.py tiger.png --use-programming-port

# Manually specify port
python3 bitmap_sender.py tiger.png /dev/ttyACM1

# Show detection info
python3 bitmap_sender.py --detect-arduino
```

### Python Code:
```python
from st7735_tools import (
    get_native_usb_port,
    get_programming_port,
    get_preferred_port
)

# Get specific port
native = get_native_usb_port()        # /dev/ttyACM1
programming = get_programming_port()   # /dev/ttyACM0

# Smart selection with fallback
port = get_preferred_port(prefer_native=True)   # Tries Native first
port = get_preferred_port(prefer_native=False)  # Tries Programming first
```

## Port Types

| Port Type | Device | Arduino Code | Behavior |
|-----------|--------|--------------|----------|
| Native USB | `/dev/ttyACM1` | `SerialUSB` | No reset on connection ✓ |
| Programming | `/dev/ttyACM0` | `Serial` | Resets on DTR toggle |

## Detection Details

The module identifies Arduino Due boards by USB VID:PID:
- **Native USB Port**: VID=2341, PID=003E
- **Programming Port**: VID=2A03/2341, PID=003D

## Test Script

Run `test_port_detection.py` to verify detection:
```bash
python3 test_port_detection.py
```

## Current Detection Results:
- Native USB: `/dev/ttyACM1` ✓
- Programming Port: `/dev/ttyACM0` ✓
