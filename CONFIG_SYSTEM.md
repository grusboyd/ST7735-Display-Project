# Display Configuration System

This project uses TOML configuration files for modular display management.

## Configuration Files

Display configurations are stored in `.config` files (TOML format):
- `DueLCD01.config` - Landscape display (158×126 usable)
- `DueLCD02.config` - Portrait display (126×158 usable)
- `display_config_template.toml` - Template for new displays

### Config File Structure

```toml
[device]
name = "DueLCD01"
manufacturer = "Unknown"
model = "Generic ST7735"
published_resolution = [160, 128]  # [width, height]

[pinout]
rst = 8
dc = 10
cs = 7
bl = 9

[calibration]
orientation = "landscape"  # landscape, portrait, reverse_landscape, reverse_portrait
left = 1
right = 158
top = 2
bottom = 127
center = [80, 65]
```

## Usage

### Python: bitmap_sender.py

List available devices:
```bash
python3 bitmap_sender.py --list-configs
```

Send image using device name:
```bash
python3 bitmap_sender.py --device DueLCD01 image.jpg
```

Send image using config file:
```bash
python3 bitmap_sender.py --config DueLCD02.config photo.png
```

### C++: Generate Header File

Generate `include/DisplayConfig.h` from config:
```bash
python3 generate_config_header.py DueLCD01.config
```

Or by device name:
```bash
python3 generate_config_header.py --device DueLCD02
```

Then in your C++ code:
```cpp
#include "DisplayConfig.h"

// Use auto-generated constants
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

void setup() {
    tft.initR(INITR_BLACKTAB);
    tft.setRotation(DISPLAY_ROTATION);
    
    // Use calibrated area
    tft.fillRect(USABLE_ORIGIN_X, USABLE_ORIGIN_Y, 
                 USABLE_WIDTH, USABLE_HEIGHT, ST77XX_WHITE);
}
```

## Python API

```python
from st7735_tools.config_loader import load_display_config, find_config_files

# Load specific config
config = load_display_config('DueLCD01.config')
print(f"{config.name}: {config.usable_width}x{config.usable_height}")

# Find all configs
configs = find_config_files()
for name, path in configs.items():
    print(f"{name}: {path}")
```

## Workflow: Calibrating a New Display

### Method 1: Using cal_lcd.cpp (Recommended)

1. **Prepare calibration tool**:
   ```bash
   cp src/main.cpp src/main.cpp.backup
   cp tools/cal_lcd.cpp src/main.cpp
   ```

2. **Upload and calibrate**:
   - Build and upload to Arduino Due
   - Open serial monitor at 115200 baud
   - Run commands:
     ```
     rot1              # Set orientation (0-3)
     frame             # Observe display boundaries
     bounds 1,158,2,127  # Set calibration values
     center            # Verify center point
     export            # Generate config file
     ```

3. **Save config file**:
   - Copy output between `BEGIN CONFIG FILE` and `END CONFIG FILE`
   - Save as `DueLCD_NEW.config` (use your device name)
   - Edit `name`, `manufacturer`, `model` fields

4. **Restore and use**:
   ```bash
   mv src/main.cpp.backup src/main.cpp
   python3 generate_config_header.py --device DueLCD_NEW
   python3 bitmap_sender.py --device DueLCD_NEW image.jpg
   ```

### Method 2: Manual Config Creation

1. **Copy template**: `cp display_config_template.toml MyDisplay.config`
2. **Manually run calibration** with existing tools
3. **Edit config file** with measured values
4. **Generate header**: `python3 generate_config_header.py --config MyDisplay.config`

### Testing

- **Python side**: `python3 bitmap_sender.py --device <name> test.jpg`
- **C++ build**: `python3 generate_config_header.py --device <name>` then build/flash

## Benefits

- **Modular**: Add new displays without editing code
- **Centralized**: Single source of truth for device specs
- **Version Control**: Config files tracked in git
- **Type-Safe**: Validated TOML format with clear structure
- **Cross-Language**: Used by both Python and C++ code
