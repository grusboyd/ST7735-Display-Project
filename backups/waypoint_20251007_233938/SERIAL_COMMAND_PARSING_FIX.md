# Serial Command Parsing Fix - Multiple Commands in Single Read

## Problem Identified

**Root Cause**: The Arduino's `Serial.readStringUntil('\n')` was receiving multiple commands in a single read operation.

### Evidence from Debug Output:
```
Arduino: BitmapReceiver: Received start command: 'BMPStart\nSIZE:157,105\n'
Arduino: BitmapReceiver: Start marker mismatch - expected 'BMPStart', got 'BMPStart\nSIZE:157,105\n'
```

### What Was Happening:
1. Python script sends `BMPStart\n` followed immediately by `SIZE:157,105\n`
2. Arduino's `readStringUntil('\n')` reads the entire buffer: `'BMPStart\nSIZE:157,105\n'`
3. Arduino expects just `'BMPStart'` but gets the combined string
4. Start marker matching fails, protocol breaks down
5. Python script times out waiting for "READY" response

## Technical Fix Implemented

### Enhanced Command Parsing:
```cpp
void handleStartMarker() {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Check if we received multiple commands in one read (contains \n)
    if (command.indexOf('\n') >= 0) {
        // Split commands and process both
        int firstNewline = command.indexOf('\n');
        String firstCommand = command.substring(0, firstNewline);
        String remainingCommand = command.substring(firstNewline + 1);
        
        // Process BMPStart
        if (firstCommand == "BMPStart") {
            currentState = WAITING_FOR_SIZE;
            
            // Process SIZE command immediately
            if (remainingCommand.startsWith("SIZE:")) {
                processSizeCommand(remainingCommand);
            }
        }
    } else {
        // Normal single command processing
        if (command == "BMPStart") {
            currentState = WAITING_FOR_SIZE;
        }
    }
}
```

### Key Improvements:
1. **Multi-Command Detection**: Checks for `\n` within received string
2. **Command Splitting**: Separates multiple commands from single read
3. **Sequential Processing**: Processes BMPStart first, then SIZE command
4. **Backward Compatibility**: Still handles single commands normally
5. **Enhanced Debugging**: Clear logging of what commands are received

## Expected Behavior After Fix

### Successful Protocol Flow:
```
Arduino: BitmapReceiver: Received start command: 'BMPStart\nSIZE:157,105\n'
Arduino: BitmapReceiver: Multiple commands detected, processing first part
Arduino: BitmapReceiver: Start marker received - transitioning to WAITING_FOR_SIZE
Arduino: BitmapReceiver: Processing remaining command: 'SIZE:157,105'
Arduino: BitmapReceiver: Parsed dimensions: 157x105
Arduino: BitmapReceiver: Dimensions validated: 157x105
Arduino: BitmapReceiver: Centering at offset (79,60)
READY
Arduino: BitmapReceiver: Receiving 157x105
Arduino: BitmapReceiver: Clearing Display 1 for bitmap reception
```

### Python Script Response:
- ✅ Receives "READY" confirmation
- ✅ Proceeds with pixel data transmission
- ✅ Completes bitmap transfer successfully
- ✅ Display 1 shows tiger image
- ✅ Display 2 frame remains stable

## Additional Debugging Added

### Frame Renderer Monitoring:
```cpp
void redrawFrame() {
    Serial.println("FrameRenderer: redrawFrame() called - this should only happen on explicit request");
    drawFrame();
}
```

This will help identify if Display 2 reinitialization is caused by unexpected `redrawFrame()` calls.

## Testing Instructions

1. **Upload the fixed firmware**
2. **Run the bitmap sender**:
   ```bash
   python3 bitmap_sender_fixed.py ./tiger.png
   ```
3. **Monitor serial output** for:
   - Successful command parsing
   - "READY" response sent
   - No unexpected frame redraws

## Root Cause Analysis

### Why This Happened:
1. **Fast Serial Transmission**: Python script sends commands quickly
2. **Arduino Buffer**: Serial buffer accumulates multiple commands
3. **Single Read Operation**: `readStringUntil('\n')` reads entire buffer
4. **String Parsing**: Simple string comparison fails with embedded newlines

### Prevention:
- Enhanced parsing handles command buffering
- More robust protocol parsing for future commands
- Clear debug output for troubleshooting

## Summary

This fix addresses the core protocol issue that was preventing bitmap transmission. The Arduino now properly handles cases where multiple commands arrive in a single serial read operation, which is common when the Python script sends commands in rapid succession.

The enhanced debugging will also help identify any remaining Display 2 reinitialization issues by tracking when and why the frame renderer is called.