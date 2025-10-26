#!/bin/bash
# Clean upload script for Arduino Due
# Ensures no serial monitors are running before upload

echo "=== Arduino Due Clean Upload Script ==="

# Step 1: Kill any running serial monitors
echo "Stopping any running serial monitors..."
pkill -f "platformio.*monitor" 2>/dev/null
pkill -f "screen.*ttyACM" 2>/dev/null
pkill -f "minicom" 2>/dev/null
pkill -f "cu.*ttyACM" 2>/dev/null

# Wait a moment for processes to terminate
sleep 1

# Step 2: Check if any processes are still running
RUNNING=$(ps aux | grep -E "(platformio.*monitor|screen.*ttyACM|minicom|cu.*ttyACM)" | grep -v grep)
if [ ! -z "$RUNNING" ]; then
    echo "Warning: Some serial processes may still be running:"
    echo "$RUNNING"
    echo "Attempting force kill..."
    pkill -9 -f "platformio.*monitor" 2>/dev/null
    pkill -9 -f "screen.*ttyACM" 2>/dev/null
    sleep 1
fi

# Step 3: Check serial port availability
if [ ! -c /dev/ttyACM0 ]; then
    echo "Error: Arduino Due not found on /dev/ttyACM0"
    echo "Available serial ports:"
    ls -la /dev/ttyACM* 2>/dev/null || echo "No ACM devices found"
    exit 1
fi

echo "Serial port /dev/ttyACM0 available"

# Step 4: Build and upload
echo "Building project..."
~/.platformio/penv/bin/platformio run
if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Uploading firmware..."
~/.platformio/penv/bin/platformio run --target upload
if [ $? -ne 0 ]; then
    echo "Upload failed!"
    exit 1
fi

echo "✅ Upload successful!"
echo "You can now start the serial monitor safely."