# ST7735 Tools Package

Python utilities for working with Arduino Due and ST7735 displays.

## Modules

### serial_utils

Arduino Due serial port detection and management.

**Functions:**
- `get_native_usb_port()` - Auto-detect Native USB port (recommended for data transfer)
- `get_programming_port()` - Get Programming port (for uploading code)
- `find_arduino_due_ports()` - Get both ports with detailed info
- `print_arduino_due_info()` - Display detection status
- `list_all_ports()` - List all available serial ports

**Classes:**
- `ArduinoDuePort` - Represents an Arduino Due serial port

## Usage

```python
from st7735_tools import get_native_usb_port, print_arduino_due_info

# Auto-detect Native USB port
port = get_native_usb_port()
if port:
    print(f"Found Native USB: {port}")

# Show detection info
print_arduino_due_info()
```

## Port Types

**Native USB Port** (`/dev/ttyACM1` or similar)
- Used with `SerialUSB` in Arduino code
- Does NOT reset the Arduino when connecting
- Recommended for data transfer

**Programming Port** (`/dev/ttyACM0` or similar)
- Used with `Serial` in Arduino code
- Resets Arduino when DTR toggles
- Used for uploading code

## Installation

No installation needed - the package is available locally in your project.

For use in other Python scripts:
```python
# Add project directory to path if needed
import sys
sys.path.insert(0, '/path/to/ST7735-Display-Project')

from st7735_tools import get_native_usb_port
```
