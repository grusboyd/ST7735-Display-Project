# ST7735 Display Calibration Tool

This directory contains the calibration tool we developed to determine the proper display bounds, origin, and usable area for ST7735 displays.

## Files
- `cal_lcd.cpp` - Complete calibration tool source code

## How to Use the Calibration Tool

1. **Backup your current main.cpp:**
   ```bash
   cp src/main.cpp src/main_backup.cpp
   ```

2. **Replace main.cpp with the calibration tool:**
   ```bash
   cp tools/cal_lcd.cpp src/main.cpp
   ```

3. **Build and upload:**
   ```bash
   platformio run --target upload
   ```

4. **Open serial monitor at 115200 baud and use commands:**
   - `rot0`, `rot1`, `rot2`, `rot3` - Test different rotations
   - `frame` - Step through frame insets to find visible bounds
   - `cross` - Draw origin-to-center line to check coordinate system
   - `test` - Run complete calibration sequence
   - `center` - Show calculated usable center
   - `info` - Display current settings
   - `help` - Show command list

5. **When done, restore the original main.cpp:**
   ```bash
   cp src/main_backup.cpp src/main.cpp
   ```

## Current Calibration Results

Based on our testing, we determined these optimal settings for the DueLCD01 configuration:

- **Rotation:** 1 (landscape mode)
- **Usable Origin:** (1, 2) - where drawing should begin
- **Usable Size:** 158 x 126 pixels - actual visible area  
- **Usable Center:** (80, 65) - calculated center of usable area

These values are already implemented in the main bitmap display code.

## Features

- **Interactive commands** - Control via serial monitor
- **Keypress pacing** - Step through tests at your own pace
- **Multiple frame insets** - Identify exact visible boundaries
- **Origin testing** - Verify coordinate system behavior
- **Rotation testing** - Find optimal display orientation
- **No auto-execution** - Only runs commands when requested

## Notes

The calibration tool helped us identify that:
1. The nominal display origin (0,0) may not be visible
2. The nominal display size includes non-visible border areas  
3. Different ST7735 variants may have different usable areas
4. Proper centering requires accounting for the actual usable area

This tool can be used for any ST7735 display to determine its specific characteristics.