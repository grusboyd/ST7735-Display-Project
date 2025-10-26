#!/bin/bash
# Safe serial monitor script for Arduino Due
# Ensures clean connection and proper monitoring

echo "=== Arduino Due Serial Monitor ==="

# Step 1: Ensure no other monitors are running
echo "Checking for existing serial monitors..."
RUNNING=$(ps aux | grep -E "(platformio.*monitor|screen.*ttyACM|minicom)" | grep -v grep)
if [ ! -z "$RUNNING" ]; then
    echo "Found running serial monitors:"
    echo "$RUNNING"
    echo -n "Stop them and continue? (y/n): "
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        pkill -f "platformio.*monitor" 2>/dev/null
        pkill -f "screen.*ttyACM" 2>/dev/null
        pkill -f "minicom" 2>/dev/null
        sleep 2
    else
        echo "Aborted."
        exit 1
    fi
fi

# Step 2: Check serial port
if [ ! -c /dev/ttyACM0 ]; then
    echo "Error: Arduino Due not found on /dev/ttyACM0"
    echo "Available serial ports:"
    ls -la /dev/ttyACM* 2>/dev/null || echo "No ACM devices found"
    exit 1
fi

# Step 3: Check if VS Code wants to use the serial monitor
echo "Serial port is available."
echo "You can now use VS Code's serial monitor or run this script."
echo -n "Start external monitor? (y/n, 'n' to use VS Code): "
read -r response
if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
    echo "Serial port freed for VS Code. Use the VS Code serial monitor now."
    exit 0
fi

echo "Starting external serial monitor on /dev/ttyACM0 at 115200 baud..."
echo "Press Ctrl+C to exit monitor"
echo "=========================================="

~/.platformio/penv/bin/platformio device monitor \
    --port /dev/ttyACM0 \
    --baud 115200 \
    --eol LF \
    --filter printable