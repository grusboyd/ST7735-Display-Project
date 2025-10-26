# Technical Documentation - ST7735 Dual Display Project

## Current Status (2025-10-08)

### Root Cause Analysis - Display 2 Reinitialization

**Problem**: Display 2 reinitializes when Display 1 receives bitmap data, causing white screen and reset.

**Root Cause**: ST77XX_SWRESET broadcast command in Adafruit ST7735 library
- SWRESET (0x01) is a hardware broadcast command
- Affects ALL ST77xx displays on shared SPI bus
- CS pin states cannot prevent broadcast commands
- Occurs during library's initR() and commonInit() functions

**Library Investigation Results**:
```cpp
// Found in Adafruit ST7735 library initialization sequences
static const uint8_t PROGMEM Bcmd[] = {
  ST77XX_SWRESET,   DELAY,  //  1: Software reset, 0 args, w/delay
    150,                    //     150 ms delay
  // ... other commands
};
```

### Solution Options Available

1. **Sequential Delayed Initialization** - Initialize displays with timing delays
2. **Hardware Pin Control** - Tie Display 2 RST pin to 3.3V to disable hardware reset
3. **Custom Library Initialization** - Create custom init sequence bypassing SWRESET
4. **Library Fork/Modification** - Modify library to make SWRESET CS-aware

*Note: Option 5 (multiplexing) tested but unsuitable for simultaneous operation*

## System Architecture

### Hardware Configuration
- **Arduino Due** with dual ST7735 1.8" TFT displays
- **Shared SPI Bus**: MOSI=11, SCK=13
- **Display 1**: CS=7, DC=10, RST=8, BL=9 (landscape mode)
- **Display 2**: CS=29, DC=31, RST=33, BL=35 (portrait mode)
- **Port C enabled** for extended pin access (pins 29, 31, 33, 35)

### Display Specifications
- **Total Resolution**: 160x128 pixels each
- **Display 1 Usable Area**: 158x126 pixels (origin at 1,2) - calibrated
- **Color Format**: RGB565
- **Communication**: Hardware SPI with individual CS control

### Software Architecture (Version 2.0.x)
- **Modular Design**: DisplayController, FeaturePolicy system
- **BitmapReceiver Class**: Handles bitmap data reception for Display 1
- **FrameRenderer Class**: Manages Display 2 frame display
- **CS Optimization**: Intelligent switching between displays

## Communication Protocol

### Bitmap Reception Protocol
```
Python Script -> Arduino:
1. "BMPStart" -> Arduino responds "READY"
2. "SIZE:width,height" -> Arduino validates and responds "READY"  
3. Pixel data (RGB565 format, chunked)
4. "BMPEnd" -> Arduino responds "COMPLETE"
```

### Serial Communication
- **Baud Rate**: 115200
- **Format**: Command strings terminated with '\n'
- **Handshaking**: Arduino sends status responses
- **Error Handling**: Timeout-based recovery (15 seconds)

## Development Workflow

### Backup Policy (Mandatory)
- Create timestamped backup before ANY modifications
- Format: `filename.backup_description_YYYYMMDD_HHMMSS`
- Maintain `main.cpp.clean` as known-good baseline

### Solution Selection Process
1. Present multiple options when available
2. Wait for explicit user selection
3. Implement only the selected approach
4. No unauthorized additions or modifications

## Build Configuration

### PlatformIO Configuration
```ini
[env:due]
platform = atmelsam
board = due
framework = arduino
```

### Dependencies
- Adafruit ST7735 and ST7789 Library v1.11.0
- Adafruit GFX Library v1.12.3
- SPI Library (built-in)

### Memory Usage (Current)
- **RAM**: ~3.2% (3232 bytes from 98304 bytes)
- **Flash**: ~11.5% (60KB from 524KB)

## Calibration Results

### Display 1 (Bitmap Display)
- **Physical Size**: 160x128 pixels
- **Usable Area**: 158x126 pixels  
- **Usable Origin**: (1, 2)
- **Mode**: Landscape (rotation 1)
- **Purpose**: Bitmap image display from Python script

### Display 2 (Frame/Clock Display)
- **Physical Size**: 160x128 pixels (in portrait: 128x160)
- **Mode**: Portrait (rotation 0)
- **Purpose**: Frame display (foundation for future clock)

## Known Issues

### Current Issue
- **Display 2 Reinitialization**: Broadcast SWRESET affects both displays
- **Status**: Root cause identified, solution pending user selection

### Resolved Issues
- ✅ Protocol mismatch between Python scripts (use bitmap_sender_fixed.py)
- ✅ Extended pin configuration for Arduino Due Port C
- ✅ Serial command parsing for multi-command scenarios
- ✅ CS timing optimization between displays

## File Structure

### Core Files
- `src/main.cpp` - Main Arduino firmware
- `bitmap_sender.py` - Original Python sender (deprecated)
- `bitmap_sender_fixed.py` - Fixed Python sender (current)
- `platformio.ini` - Build configuration

### Utilities
- `tools/cal_lcd.cpp` - Display calibration utility
- `monitor.sh` - Serial monitoring script
- Various shell scripts for build/upload automation

### Documentation  
- `README.md` - Project overview
- `CHANGELOG.md` - Complete change history
- `WORKFLOW.md` - Development workflow policy
- `tools/README.md` - Calibration tool guide

### Test Assets
- `tiger.png` - Test image file
- Various backup files with timestamps

## Future Development

### Planned Features
- Clock display on Display 2 (analog or digital)
- Multiple display modes and patterns
- Enhanced bitmap processing capabilities

### Technical Debt
- Library dependency on broadcast SWRESET command
- Multiple redundant documentation files (cleanup in progress)
- Development session transcripts and temporary files

This technical documentation consolidates information from multiple previous analysis documents and provides a comprehensive reference for the project's current state and architecture.