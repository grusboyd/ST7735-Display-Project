# Multi-Display Modular Workflow (v3.0)

## Overview

**v3.0** introduces a multi-display architecture where a single firmware supports multiple displays with runtime selection via serial protocol. This builds on the v2.1.0 modular configuration system (TOML files and header generation).

### Key Concepts

- **v2.1.0 Config System**: TOML `.config` files define display parameters (pins, calibration)
- **v3.0 Multi-Display**: Single firmware manages multiple displays, selected at runtime
- **No Recompilation**: Switch between displays via serial commands without rebuilding

## Architecture Components

### DisplayManager Library
- **Purpose**: Manage multiple displays with registration and validation
- **Location**: `lib/DisplayManager/`
- **Features**:
  - Register up to 8 displays by name
  - Pin conflict detection
  - Test pattern rendering (gradient + calibration frame + device info)
  - Runtime display lookup by name

### SerialProtocol Library
- **Purpose**: Handle bitmap transmission with multi-display support
- **Location**: `lib/SerialProtocol/`
- **Features**:
  - Display selection: `DISPLAY:<name>` command
  - Bitmap protocol: BMPStart → SIZE → pixels → BMPEnd
  - Error recovery: automatic timeout reset + manual RESET command
  - Progress reporting during pixel reception

## Quick Start (v3.0)

### 1. Build and Upload Firmware

```bash
# Build multi-display firmware (supports all registered displays)
platformio run

# Upload to Arduino Due
platformio run --target upload
```

The firmware initializes all registered displays and shows test patterns on each.

### 2. Send Images to Specific Display

```bash
# Select display and send image
python3 bitmap_sender.py --device DueLCD01 tiger.png /dev/ttyACM0

# Switch to different display (no rebuild needed!)
python3 bitmap_sender.py --device DueLCD02 photo.jpg /dev/ttyACM0
```

### 3. Manual Protocol Control

Connect via serial monitor (115200 baud) and use commands:

```
DISPLAY:DueLCD01       # Select display
DISPLAY_READY:DueLCD01 # Response from Arduino

BMPStart               # Begin bitmap transmission
SIZE:158,126          # Specify dimensions
READY                 # Arduino is ready

[pixel data]          # Send RGB565 pixels

BMPEnd                # End transmission
COMPLETE              # Arduino confirms

RESET                 # Manual reset (if needed)
```

## Adding New Displays (v2.1.0 + v3.0)

### Step 1: Calibrate Display (v2.1.0 workflow)
> rot1                    # Set rotation (0-3)
> frame                   # Draw test frame
> bounds 1,158,2,127      # Set calibrated bounds
> center                  # Verify center point
> export                  # Generate TOML config
```

### Step 1: Calibrate Display (v2.1.0 workflow)

Use the calibration tool to determine display parameters:

```bash
# Calibration session via serial monitor:
> rot1                    # Set rotation (0-3)
> frame                   # Draw test frame
> bounds 1,158,2,127      # Set calibrated bounds
> center                  # Verify center point
> export                  # Generate TOML config
```

### Step 2: Save Config File (v2.1.0)

Copy exported TOML and save as `MyNewDisplay.config`:

```toml
[device]
name = "MyNewDisplay"
manufacturer = "Adafruit"
model = "ST7735"
published_resolution = [160, 128]

[pinout]
rst = 33
dc = 31
cs = 29
bl = 35

[calibration]
orientation = "portrait"
left = 2
right = 127
top = 1
bottom = 158
center = [65, 80]
```

### Step 3: Register Display (v3.0)

Add display to `src/main.cpp`:

```cpp
void setup() {
    // Initialize SPI
    SPI.begin();
    
    // Register existing displays
    displayManager.registerDisplay("DueLCD01", 7, 10, 8, 9, 158, 126, 1);
    displayManager.registerDisplay("DueLCD02", 29, 31, 33, 35, 126, 158, 0);
    
    // Register new display
    displayManager.registerDisplay("MyNewDisplay", 29, 31, 33, 35, 158, 126, 0);
    
    // Initialize all displays
    displayManager.initializeAll();
}
```

### Step 4: Build and Use (v3.0)

```bash
# Build with new display registered
platformio run --target upload

# Send images to new display
python3 bitmap_sender.py --device MyNewDisplay image.png /dev/ttyACM0
```

## v3.0 vs v2.1.0 Workflow Comparison

### v2.1.0: Single Display per Build
1. Generate header: `python3 generate_config_header.py --device DueLCD01`
2. Build: `platformio run`
3. Upload: `platformio run --target upload`
4. Send image: `python3 bitmap_sender.py --device DueLCD01 image.png`
5. **To switch displays**: Regenerate header, rebuild, re-upload (steps 1-3 again)

### v3.0: Multi-Display Runtime Selection
1. Build once: `platformio run --target upload`
2. Send to Display 1: `python3 bitmap_sender.py --device DueLCD01 image.png`
3. **To switch displays**: `python3 bitmap_sender.py --device DueLCD02 image.png`
4. **No rebuild needed!**

## Protocol Details

### Display Selection Phase

### Display Selection Phase

Client sends: `DISPLAY:<name>`
Arduino responds: `DISPLAY_READY:<name>` or `ERROR: Display not found`

### Bitmap Transmission Phase

1. Client: `BMPStart`
2. Arduino: `"Start marker received"`
3. Client: `SIZE:width,height`
4. Arduino: Clears display, sends `READY`
5. Client: Sends RGB565 pixel data (2 bytes per pixel)
6. Arduino: Progress updates every 10 rows
7. Client: `BMPEnd`
8. Arduino: `COMPLETE`, ready for next bitmap

### Error Recovery

**Automatic**: 15-second timeout triggers protocol reset
**Manual**: Send `RESET` command anytime during display selection

## Test Patterns

Each display shows test pattern on initialization:
- **Horizontal gradient**: Blue (left) to red (right)
- **Calibration frame**: White border showing usable area
- **Device info**: Display name, resolution, orientation (black text)

Test patterns verify:
- Display is working
- Orientation is correct
- Calibration bounds are accurate
- Text rendering is readable

## Code Quality Features (v3.0)

### Constants (SerialProtocol)
- `TIMEOUT_MS = 15000` - Inactivity timeout
- `DISPLAY_SELECT_TIMEOUT = 3000` - Display selection timeout
- `READY_TIMEOUT = 5000` - Ready response timeout
- `MAX_DIMENSION = 1000` - Maximum width/height
- `PROGRESS_REPORT_INTERVAL = 10` - Report every N rows

### Validation (DisplayManager)
- Pin conflict detection (CS/DC/RST pins)
- Duplicate display name checking
- Dimension validation (1-1000 pixels)
- Rotation validation (0-3)

### Optimization
- Gradient rendering: Precomputed inverse width
- Const correctness: Explicit float literals
- Error handling: Active display validation

## Library Structure

```
lib/
├── DisplayManager/
│   ├── DisplayManager.h         # Interface (91 lines)
│   ├── DisplayManager.cpp       # Implementation (251 lines)
│   └── library.json            # PlatformIO metadata
└── SerialProtocol/
    ├── SerialProtocol.h         # Interface (91 lines)
    ├── SerialProtocol.cpp       # Implementation (370 lines)
    └── library.json            # PlatformIO metadata

src/
└── main.cpp                     # 85 lines (78% reduction from v2.1.0)
```

## Main.cpp Structure (v3.0)

```cpp
#include <SPI.h>
#include <DisplayManager.h>
#include <SerialProtocol.h>

DisplayManager displayManager;
SerialProtocol* protocol = nullptr;

void setup() {
    SerialUSB.begin(115200);
    SPI.begin();
    
    // Register all displays
    displayManager.registerDisplay("DueLCD01", 7, 10, 8, 9, 158, 126, 1);
    displayManager.registerDisplay("DueLCD02", 29, 31, 33, 35, 126, 158, 0);
    
    // Initialize and show test patterns
    displayManager.initializeAll();
    
    // Create protocol handler
    protocol = new SerialProtocol(displayManager, SerialUSB);
    
    SerialUSB.println("Multi-Display System Ready");
}

void loop() {
    protocol->process();      // Handle serial commands
    protocol->checkTimeout(); // Monitor for timeouts
}
```

## Benefits of v3.0 Architecture

✅ **78% Code Reduction**: main.cpp shrunk from 379 to 85 lines
✅ **No Recompilation**: Switch displays via serial commands
✅ **Reusable Libraries**: DisplayManager and SerialProtocol are modular
✅ **Error Recovery**: Automatic timeout handling + manual reset
✅ **Validation**: Pin conflicts, dimensions, duplicate names
✅ **Extensible**: Easy to add new displays or features
✅ **Maintainable**: Clear separation of concerns

## Troubleshooting

## Troubleshooting

### Display Not Found

Check display is registered in `src/main.cpp`:
```cpp
displayManager.registerDisplay("YourDisplayName", ...);
```

### Protocol Timeout

Arduino automatically resets after 15 seconds of inactivity. Check:
- Serial connection is stable
- Python script is sending data continuously
- No USB cable issues

Manual reset: Send `RESET` command via serial monitor

### Wrong Display Responding

Verify display selection command:
```bash
python3 bitmap_sender.py --device CorrectDisplayName image.png
```

### Pin Conflicts

DisplayManager validates pins during registration. Check serial output for:
```
ERROR: Pin conflict detected - CS pin 7 already used
```

Solution: Use different pins for each display

## Migration from v2.1.0

### What Stays the Same
- TOML `.config` files still used for display parameters
- `bitmap_sender.py --device` command still works
- Calibration workflow unchanged
- Config file format unchanged

### What's New in v3.0
- Single firmware supports multiple displays (no regenerate header)
- DisplayManager library manages display registration
- SerialProtocol library handles bitmap transmission
- Test patterns show on initialization
- Error recovery with timeout handling
- 78% smaller main.cpp (85 vs 379 lines)

### Upgrade Path
1. Keep existing `.config` files (DueLCD01.config, DueLCD02.config)
2. Update `src/main.cpp` to register all displays
3. Build and upload v3.0 firmware
4. Use same Python commands (`bitmap_sender.py --device <name>`)
5. Enjoy runtime display switching without rebuilding!

## See Also

- `CHANGELOG.md` - Complete version history (v2.1.0 and v3.0)
- `CONFIG_SYSTEM.md` - v2.1.0 config file documentation
- `tools/CALIBRATION_GUIDE.md` - Calibration tool reference
- `lib/DisplayManager/DisplayManager.h` - DisplayManager API
- `lib/SerialProtocol/SerialProtocol.h` - SerialProtocol API
````

## See Also

- `CONFIG_SYSTEM.md` - Complete config system documentation
- `tools/CALIBRATION_GUIDE.md` - Calibration tool command reference
- `CHANGELOG.md` - Version history (see v2.1.0)
