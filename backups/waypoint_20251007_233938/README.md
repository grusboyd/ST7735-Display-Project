# ST7735 Display Project

A bitmap display system using an ST7735 LCD display connected to an Arduino Due, with image processing and transmission handled by a Raspberry Pi.

## Features

- 158x126 usable display area (from 160x128 total)
- RGB565 color format
- Automatic image scaling and centering
- Real-time serial communication
- Interactive calibration system
- Comprehensive error handling and validation

## Hardware Requirements

- **ST7735 1.8" TFT LCD Display** (160x128 pixels)
- **Arduino Due**
- **Raspberry Pi** (for image processing)
- **USB cable** for serial communication

## Pin Configuration

- CS = 7 (Chip Select)
- DC = 10 (Data/Command)
- RST = 8 (Reset)
- BL = 9 (Backlight)

## Project Structure

```
ST7735onDue/
├── src/
│   └── main.cpp              # Main Arduino display code
├── tools/
│   └── cal_lcd.cpp           # Interactive calibration tool
├── platformio.ini            # PlatformIO configuration
└── README.md                 # This file
```

## Quick Start

1. **Upload Arduino Code**:
   ```bash
   platformio run --target upload
   ```

2. **Run Image Sender** (on Raspberry Pi):
   ```bash
   python3 bitmap_sender.py /path/to/image.png
   ```

## Display Specifications

- **Total Resolution**: 160x128 pixels
- **Usable Area**: 158x126 pixels (origin at 1,2)
- **Color Format**: RGB565
- **Orientation**: Landscape (automatic rotation handled)

## Calibration

The project includes an interactive calibration tool (`tools/cal_lcd.cpp`) for precise display boundary determination. Key calibrated values:

- Usable display area: 158x126 pixels
- Display origin offset: (1,2)
- Frame boundaries validated through interactive testing

## Development

Built with:
- **PlatformIO** for Arduino development
- **Adafruit ST7735 Library** for display control
- **Python PIL** for image processing
- **Serial communication** for data transmission

## Author

- **grusboyd** <crank.drive@protonmail.com>

## License

MIT License - See LICENSE file for details.
