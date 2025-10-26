#!/bin/bash
# Cleanup script for VS Code Serial Monitor
# Stops external monitors so VS Code can connect

echo "=== Preparing for VS Code Serial Monitor ==="

# Kill any external serial monitors
echo "Stopping external serial monitors..."
pkill -f "platformio.*monitor" 2>/dev/null
pkill -f "screen.*ttyACM" 2>/dev/null  
pkill -f "minicom" 2>/dev/null
pkill -f "cu.*ttyACM" 2>/dev/null

# Wait for processes to terminate
sleep 2

# Force kill if needed
pkill -9 -f "platformio.*monitor" 2>/dev/null
pkill -9 -f "screen.*ttyACM" 2>/dev/null
sleep 1

# Check if port is free
if lsof /dev/ttyACM0 >/dev/null 2>&1; then
    echo "Warning: Something is still using /dev/ttyACM0"
    echo "Processes using the port:"
    lsof /dev/ttyACM0
    echo ""
    echo "Try unplugging and reconnecting the Arduino Due"
else
    echo "✅ Serial port /dev/ttyACM0 is now free"
    echo "You can now use VS Code's Serial Monitor"
    echo ""
    echo "In VS Code:"
    echo "1. Open Command Palette (Ctrl+Shift+P)"
    echo "2. Type 'Serial Monitor'"
    echo "3. Select port /dev/ttyACM0"
    echo "4. Set baud rate to 115200"
fi