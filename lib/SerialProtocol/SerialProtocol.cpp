/*
 * SerialProtocol.cpp
 * Implementation of bitmap transmission protocol
 */

#include "SerialProtocol.h"

SerialProtocol::SerialProtocol(DisplayManager& displayMgr, Stream& serial)
    : displayManager(displayMgr)
    , serialPort(serial)
    , currentState(WAITING_FOR_DISPLAY_SELECT)
    , activeDisplay(nullptr)
    , bitmapWidth(0)
    , bitmapHeight(0)
    , currentRow(0)
    , currentCol(0)
    , offsetX(0)
    , offsetY(0)
    , lastActivity(0)
    , imageFrameEnabled(true)
    , imageFrameColor(ST77XX_WHITE)
    , imageFrameThickness(1)
    , usableAreaAdjustTop(0)
    , usableAreaAdjustBottom(0)
    , usableAreaAdjustLeft(0)
    , usableAreaAdjustRight(0) {
}

void SerialProtocol::process() {
    if (!serialPort.available()) {
        return;
    }
    
    lastActivity = millis();
    
    switch (currentState) {
        case WAITING_FOR_DISPLAY_SELECT:
            handleDisplaySelect();
            break;
            
        case WAITING_FOR_START:
            handleStart();
            break;
            
        case WAITING_FOR_SIZE:
            handleSize();
            break;
            
        case RECEIVING_DATA:
            handleDataReception();
            break;
            
        case WAITING_FOR_END:
            handleEnd();
            break;
            
        case BITMAP_COMPLETE:
            handleComplete();
            break;
    }
}

void SerialProtocol::handleDisplaySelect() {
    unsigned long startTime = millis();
    String displayName = "";
    
    // Give a short time for a command to arrive
    while (serialPort.available() || (millis() - startTime < DISPLAY_SELECT_TIMEOUT)) {
        if (serialPort.available()) {
            String command = serialPort.readStringUntil('\n');
            command.trim();
            
            // Handle CMD: commands
            if (command.startsWith("CMD:")) {
                handleMenuCommand(command.substring(4));
                return;
            }
            
            // Handle RESET command
            if (command == "RESET") {
                reset();
                serialPort.println("Protocol reset");
                return;
            }
            
            // Handle FRAME commands
            if (command.startsWith("FRAME:")) {
                String frameCmd = command.substring(6);
                
                if (frameCmd == "ON") {
                    imageFrameEnabled = true;
                    serialPort.println("Frame enabled");
                } else if (frameCmd == "OFF") {
                    imageFrameEnabled = false;
                    serialPort.println("Frame disabled");
                } else if (frameCmd.startsWith("COLOR:")) {
                    // Parse color value (e.g., "COLOR:31" for blue)
                    String colorStr = frameCmd.substring(6);
                    imageFrameColor = colorStr.toInt();
                    serialPort.print("Frame color set to: ");
                    serialPort.println(imageFrameColor);
                } else if (frameCmd.startsWith("THICKNESS:")) {
                    // Parse thickness value (e.g., "THICKNESS:2")
                    String thickStr = frameCmd.substring(10);
                    imageFrameThickness = thickStr.toInt();
                    serialPort.print("Frame thickness set to: ");
                    serialPort.println(imageFrameThickness);
                }
                return;
            }
            
            // Handle DISPLAY: command (bitmap protocol)
            if (command.startsWith("DISPLAY:")) {
                displayName = command.substring(8);
                displayName.trim();
                
                // Look up display by name
                activeDisplay = displayManager.getDisplay(displayName.c_str());
                
                if (activeDisplay) {
                    serialPort.print("DISPLAY_READY:");
                    serialPort.println(displayName);
                    currentState = WAITING_FOR_START;
                    lastActivity = millis();
                    return;
                } else {
                    sendError("Display not found: " + displayName);
                    return;
                }
            }
        }
        delay(10);
    }
    
    // Timeout waiting for display selection
    if (displayName.length() == 0) {
        serialPort.println("Ready for next bitmap");
    }
}

void SerialProtocol::handleMenuCommand(const String& command) {
    // Handle menu/control commands (CMD: prefix already stripped)
    String cmd = command;
    cmd.trim();
    
    if (cmd == "RESET") {
        // Reset protocol state
        reset();
        serialPort.println("OK:Protocol reset");
        
    } else if (cmd == "LIST") {
        // List all registered displays
        serialPort.println("OK:DISPLAY_LIST");
        int count = displayManager.getDisplayCount();
        serialPort.print("Count:");
        serialPort.println(count);
        
        // Use DisplayManager's listDisplays method
        displayManager.listDisplays(serialPort);
        
        serialPort.println("END_LIST");
        
    } else if (cmd == "INFO") {
        // Show active display info
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        const DisplayConfig& cfg = activeDisplay->getConfig();
        serialPort.println("OK:DISPLAY_INFO");
        serialPort.print("Name:");
        serialPort.println(cfg.name);
        serialPort.print("Resolution:");
        serialPort.print(cfg.usableWidth);
        serialPort.print("x");
        serialPort.println(cfg.usableHeight);
        serialPort.print("Rotation:");
        serialPort.println(cfg.rotation);
        serialPort.print("FrameEnabled:");
        serialPort.println(imageFrameEnabled ? "Yes" : "No");
        serialPort.print("FrameColor:");
        serialPort.println(imageFrameColor);
        serialPort.print("FrameThickness:");
        serialPort.println(imageFrameThickness);
        serialPort.print("UsableAreaAdjustTop:");
        serialPort.println(usableAreaAdjustTop);
        serialPort.print("UsableAreaAdjustBottom:");
        serialPort.println(usableAreaAdjustBottom);
        serialPort.print("UsableAreaAdjustLeft:");
        serialPort.println(usableAreaAdjustLeft);
        serialPort.print("UsableAreaAdjustRight:");
        serialPort.println(usableAreaAdjustRight);
        serialPort.print("CenterX:");
        serialPort.println(cfg.centerX);
        serialPort.print("CenterY:");
        serialPort.println(cfg.centerY);
        serialPort.println("END_INFO");
        
    } else if (cmd == "TEST") {
        // Test active display
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        serialPort.print("OK:Testing display ");
        serialPort.println(activeDisplay->getName());
        activeDisplay->showTestPattern();
        serialPort.println("Test pattern displayed");
        
    } else if (cmd == "TEST_ALL") {
        // Test all displays
        serialPort.println("OK:Testing all displays");
        displayManager.showAllTestPatterns();
        serialPort.println("All test patterns displayed");
        
    } else if (cmd == "FRAME_ON") {
        // Enable frame on active display
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        activeDisplay->enableImageFrame(true, imageFrameColor, imageFrameThickness,
                                       usableAreaAdjustTop, usableAreaAdjustBottom,
                                       usableAreaAdjustLeft, usableAreaAdjustRight);
        imageFrameEnabled = true;
        serialPort.println("OK:Frame enabled");
        
    } else if (cmd == "FRAME_OFF") {
        // Disable frame on active display
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        activeDisplay->enableImageFrame(false);
        imageFrameEnabled = false;
        serialPort.println("OK:Frame disabled");
        
    } else if (cmd.startsWith("FRAME_COLOR:")) {
        // Set frame color
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String colorStr = cmd.substring(12);
        uint16_t color = colorStr.toInt();
        imageFrameColor = color;
        imageFrameEnabled = true;
        serialPort.print("OK:Frame color set to ");
        serialPort.println(color);
        
        // Immediately update display with new color
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           color, imageFrameThickness);
        
    } else if (cmd.startsWith("FRAME_THICKNESS:")) {
        // Set frame thickness
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String thickStr = cmd.substring(16);
        int thickness = thickStr.toInt();
        
        if (thickness < 1 || thickness > 10) {
            serialPort.println("ERROR:Thickness must be between 1 and 10");
            return;
        }
        
        imageFrameThickness = thickness;
        imageFrameEnabled = true;
        serialPort.print("OK:Frame thickness set to ");
        serialPort.println(thickness);
        
        // Immediately update display with new thickness
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           imageFrameColor, thickness);
        
    } else if (cmd.startsWith("ADJUST_TOP:")) {
        // Adjust usable area top edge
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String adjustStr = cmd.substring(11);
        int8_t adjust = adjustStr.toInt();
        
        const DisplayConfig& cfg = activeDisplay->getConfig();
        // Top is inverted: positive adjustment moves edge UP (decreases Y)
        int newTop = cfg.usableY - adjust;
        
        // Inner bound: center - 10 pixels
        // Outer bound: -10 pixels (10 pixels beyond published top edge)
        int innerBound = cfg.centerY - 10;
        int outerBound = -10;
        
        if (newTop < outerBound) {
            serialPort.print("ERROR:Top edge would be beyond limit (maximum adjustment: ");
            serialPort.print(cfg.usableY - outerBound);
            serialPort.println(")");
            return;
        }
        
        if (newTop > innerBound) {
            serialPort.print("ERROR:Top edge would be past center-10 (minimum adjustment: ");
            serialPort.print(cfg.usableY - innerBound);
            serialPort.println(")");
            return;
        }
        
        usableAreaAdjustTop = adjust;
        serialPort.print("OK:Top edge adjusted to ");
        serialPort.println(adjust);
        
        // Notify if at outer limit
        if (newTop <= -10) {
            serialPort.println("NOTICE:Top edge at maximum outward position (-10 pixels beyond display)");
        }
        
        // Immediately update display
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           imageFrameColor, imageFrameThickness);
        
    } else if (cmd.startsWith("ADJUST_BOTTOM:")) {
        // Adjust usable area bottom edge
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String adjustStr = cmd.substring(14);
        int8_t adjust = adjustStr.toInt();
        
        const DisplayConfig& cfg = activeDisplay->getConfig();
        int configBottom = cfg.usableY + cfg.usableHeight - 1;
        int newBottom = configBottom + adjust;
        
        // Inner bound: center + 10 pixels
        // Outer bound: height + 10 - 1 (10 pixels beyond published bottom edge)
        int innerBound = cfg.centerY + 10;
        int outerBound = cfg.height + 10 - 1;
        
        if (newBottom > outerBound) {
            serialPort.print("ERROR:Bottom edge would be beyond limit (maximum: ");
            serialPort.print(outerBound - configBottom);
            serialPort.println(")");
            return;
        }
        
        if (newBottom < innerBound) {
            serialPort.print("ERROR:Bottom edge would be past center+10 (minimum: ");
            serialPort.print(innerBound - configBottom);
            serialPort.println(")");
            return;
        }
        
        usableAreaAdjustBottom = adjust;
        serialPort.print("OK:Bottom edge adjusted to ");
        serialPort.println(adjust);
        
        // Notify if at outer limit
        if (newBottom >= cfg.height + 10 - 1) {
            serialPort.print("NOTICE:Bottom edge at maximum outward position (");
            serialPort.print(cfg.height + 10 - 1);
            serialPort.println(" pixels, 10 beyond display)");
        }
        
        // Immediately update display
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           imageFrameColor, imageFrameThickness);
        
    } else if (cmd.startsWith("ADJUST_LEFT:")) {
        // Adjust usable area left edge
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String adjustStr = cmd.substring(12);
        int8_t adjust = adjustStr.toInt();
        
        const DisplayConfig& cfg = activeDisplay->getConfig();
        // Left is inverted: positive adjustment moves edge LEFT (decreases X)
        int newLeft = cfg.usableX - adjust;
        
        // Inner bound: center - 10 pixels
        // Outer bound: -10 pixels (10 pixels beyond published left edge)
        int innerBound = cfg.centerX - 10;
        int outerBound = -10;
        
        if (newLeft < outerBound) {
            serialPort.print("ERROR:Left edge would be beyond limit (maximum adjustment: ");
            serialPort.print(cfg.usableX - outerBound);
            serialPort.println(")");
            return;
        }
        
        if (newLeft > innerBound) {
            serialPort.print("ERROR:Left edge would be past center-10 (minimum adjustment: ");
            serialPort.print(cfg.usableX - innerBound);
            serialPort.println(")");
            return;
        }
        
        usableAreaAdjustLeft = adjust;
        serialPort.print("OK:Left edge adjusted to ");
        serialPort.println(adjust);
        
        // Notify if at outer limit
        if (newLeft <= -10) {
            serialPort.println("NOTICE:Left edge at maximum outward position (-10 pixels beyond display)");
        }
        
        // Immediately update display
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           imageFrameColor, imageFrameThickness);
        
    } else if (cmd.startsWith("ADJUST_RIGHT:")) {
        // Adjust usable area right edge
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String adjustStr = cmd.substring(13);
        int8_t adjust = adjustStr.toInt();
        
        const DisplayConfig& cfg = activeDisplay->getConfig();
        int configRight = cfg.usableX + cfg.usableWidth - 1;
        int newRight = configRight + adjust;
        
        // Inner bound: center + 10 pixels
        // Outer bound: width + 10 - 1 (10 pixels beyond published right edge)
        int innerBound = cfg.centerX + 10;
        int outerBound = cfg.width + 10 - 1;
        
        if (newRight > outerBound) {
            serialPort.print("ERROR:Right edge would be beyond limit (maximum: ");
            serialPort.print(outerBound - configRight);
            serialPort.println(")");
            return;
        }
        
        if (newRight < innerBound) {
            serialPort.print("ERROR:Right edge would be past center+10 (minimum: ");
            serialPort.print(innerBound - configRight);
            serialPort.println(")");
            return;
        }
        
        usableAreaAdjustRight = adjust;
        serialPort.print("OK:Right edge adjusted to ");
        serialPort.println(adjust);
        
        // Notify if at outer limit
        if (newRight >= cfg.width + 10 - 1) {
            serialPort.print("NOTICE:Right edge at maximum outward position (");
            serialPort.print(cfg.width + 10 - 1);
            serialPort.println(" pixels, 10 beyond display)");
        }
        
        // Immediately update display
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           imageFrameColor, imageFrameThickness);
        
    } else if (cmd == "CALIBRATE") {
        // Show calibration pattern on active display
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        serialPort.print("OK:Showing calibration pattern on ");
        serialPort.println(activeDisplay->getName());
        activeDisplay->drawCalibrationFrame(usableAreaAdjustTop, usableAreaAdjustBottom,
                                           usableAreaAdjustLeft, usableAreaAdjustRight,
                                           imageFrameColor, imageFrameThickness);
        serialPort.println("Calibration pattern displayed");
        
    } else if (cmd.startsWith("UPDATE_CONFIG:")) {
        // Update base configuration values
        // Format: UPDATE_CONFIG:left,right,top,bottom,centerX,centerY
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        String params = cmd.substring(14);  // Skip "UPDATE_CONFIG:"
        int values[6];
        int idx = 0;
        int start = 0;
        
        // Parse comma-separated values
        for (int i = 0; i <= params.length(); i++) {
            if (i == params.length() || params.charAt(i) == ',') {
                if (idx >= 6) {
                    serialPort.println("ERROR:Too many parameters");
                    return;
                }
                values[idx++] = params.substring(start, i).toInt();
                start = i + 1;
            }
        }
        
        if (idx != 6) {
            serialPort.println("ERROR:Expected 6 parameters (left,right,top,bottom,centerX,centerY)");
            return;
        }
        
        // Update the display's configuration
        DisplayConfig& cfg = const_cast<DisplayConfig&>(activeDisplay->getConfig());
        cfg.usableX = values[0];  // left
        cfg.usableWidth = values[1] - values[0] + 1;  // width from right-left+1
        cfg.usableY = values[2];  // top
        cfg.usableHeight = values[3] - values[2] + 1;  // height from bottom-top+1
        cfg.centerX = values[4];
        cfg.centerY = values[5];
        
        // Reset adjustments since we're committing to new base config
        usableAreaAdjustTop = 0;
        usableAreaAdjustBottom = 0;
        usableAreaAdjustLeft = 0;
        usableAreaAdjustRight = 0;
        
        serialPort.println("OK:Base configuration updated");
        serialPort.print("New usable area: ");
        serialPort.print(cfg.usableX);
        serialPort.print(",");
        serialPort.print(cfg.usableX + cfg.usableWidth - 1);
        serialPort.print(",");
        serialPort.print(cfg.usableY);
        serialPort.print(",");
        serialPort.println(cfg.usableY + cfg.usableHeight - 1);
        serialPort.print("New center: ");
        serialPort.print(cfg.centerX);
        serialPort.print(",");
        serialPort.println(cfg.centerY);
        serialPort.println("NOTE:Changes lost on power cycle - update .config file for permanent storage");
        
    } else if (cmd.startsWith("ORIENTATION:")) {
        // Set display orientation/rotation
        // Format: ORIENTATION:value (0-3)
        if (!activeDisplay) {
            serialPort.println("ERROR:No active display selected");
            return;
        }
        
        int rotation = cmd.substring(12).toInt();  // Skip "ORIENTATION:"
        
        if (rotation < 0 || rotation > 3) {
            serialPort.println("ERROR:Invalid orientation. Use 0-3 (0=Portrait, 1=Landscape, 2=Reverse Portrait, 3=Reverse Landscape)");
            return;
        }
        
        Adafruit_ST7735* tft = activeDisplay->getTFT();
        if (!tft) {
            serialPort.println("ERROR:Display not initialized");
            return;
        }
        
        tft->setRotation(rotation);
        serialPort.print("OK:Orientation set to ");
        serialPort.println(rotation);
        
    } else if (cmd == "HELP") {
        // Show command help
        serialPort.println("OK:HELP");
        serialPort.println("Available CMD: commands:");
        serialPort.println("  CMD:LIST - List all displays");
        serialPort.println("  CMD:INFO - Show active display info");
        serialPort.println("  CMD:TEST - Test active display");
        serialPort.println("  CMD:TEST_ALL - Test all displays");
        serialPort.println("  CMD:FRAME_ON - Enable frame");
        serialPort.println("  CMD:FRAME_OFF - Disable frame");
        serialPort.println("  CMD:FRAME_COLOR:value - Set frame color (0-65535)");
        serialPort.println("  CMD:FRAME_THICKNESS:value - Set thickness (1-10)");
        serialPort.println("  CMD:ADJUST_TOP:value - Adjust top edge (relative to config)");
        serialPort.println("  CMD:ADJUST_BOTTOM:value - Adjust bottom edge");
        serialPort.println("  CMD:ADJUST_LEFT:value - Adjust left edge");
        serialPort.println("  CMD:ADJUST_RIGHT:value - Adjust right edge");
        serialPort.println("  CMD:CALIBRATE - Show calibration pattern");
        serialPort.println("  CMD:UPDATE_CONFIG:left,right,top,bottom,centerX,centerY - Update base config");
        serialPort.println("  CMD:ORIENTATION:value - Set rotation (0=Portrait, 1=Landscape, 2=Rev Portrait, 3=Rev Landscape)");
        serialPort.println("  CMD:HELP - Show this help");
        serialPort.println();
        serialPort.println("Bitmap protocol commands:");
        serialPort.println("  DISPLAY:<name> - Select display for bitmap");
        serialPort.println("  BMPStart - Start bitmap transfer");
        serialPort.println("  SIZE:width,height - Set bitmap dimensions");
        serialPort.println("  <pixel data> - Send RGB565 pixel data");
        serialPort.println("  BMPEnd - End bitmap transfer");
        serialPort.println("END_HELP");
        
    } else {
        serialPort.print("ERROR:Unknown command: ");
        serialPort.println(cmd);
    }
}

void SerialProtocol::handleStart() {
    // Ensure we have an active display before accepting bitmap
    if (!activeDisplay) {
        sendError("No active display selected");
        currentState = WAITING_FOR_DISPLAY_SELECT;
        return;
    }
    
    String command = serialPort.readStringUntil('\n');
    command.trim();
    
    // Handle CMD: commands in any state
    if (command.startsWith("CMD:")) {
        handleMenuCommand(command.substring(4));
        return;
    }
    
    if (command == "BMPStart") {
        serialPort.println("Start marker received");
        currentState = WAITING_FOR_SIZE;
    } else if (command.length() > 0) {
        sendError("Expected BMPStart, got: " + command);
    }
}

void SerialProtocol::handleSize() {
    String sizeCommand = serialPort.readStringUntil('\n');
    sizeCommand.trim();
    
    if (sizeCommand.startsWith("SIZE:")) {
        int commaIndex = sizeCommand.indexOf(',');
        if (commaIndex > 0) {
            bitmapWidth = sizeCommand.substring(5, commaIndex).toInt();
            bitmapHeight = sizeCommand.substring(commaIndex + 1).toInt();
            
            if (validateDimensions(bitmapWidth, bitmapHeight) && 
                calculateOffsets(bitmapWidth, bitmapHeight, offsetX, offsetY)) {
                
                // Clear display BEFORE sending READY
                if (activeDisplay) {
                    serialPort.println("Clearing display...");
                    activeDisplay->getTFT()->fillScreen(ST77XX_BLACK);
                    delay(50);  // Brief delay to ensure clear completes
                }
                
                serialPort.println("READY");
                serialPort.print("Receiving bitmap: ");
                serialPort.print(bitmapWidth);
                serialPort.print("x");
                serialPort.println(bitmapHeight);
                
                currentRow = 0;
                currentCol = 0;
                currentState = RECEIVING_DATA;
                
                serialPort.print("Ready to receive ");
                serialPort.print(bitmapWidth * bitmapHeight);
                serialPort.println(" pixels");
            }
        } else {
            sendError("Invalid size format");
        }
    }
}

void SerialProtocol::handleDataReception() {
    if (!activeDisplay) {
        sendError("No active display");
        return;
    }
    
    Adafruit_ST7735* tft = activeDisplay->getTFT();
    
    // Read pixel data (2 bytes per pixel for RGB565)
    while (serialPort.available() >= 2 && currentState == RECEIVING_DATA) {
        if (currentRow >= bitmapHeight) {
            currentState = WAITING_FOR_END;
            break;
        }
        
        // Read RGB565 pixel data (big-endian)
        uint8_t highByte = serialPort.read();
        uint8_t lowByte = serialPort.read();
        uint16_t pixelColor = (highByte << 8) | lowByte;
        
        // Calculate pixel position
        int displayX = currentCol + offsetX;
        int displayY = currentRow + offsetY;
        
        // Draw pixel with frame bounds checking (acts as cropping guide)
        // Frame adjustments define the visible area regardless of frame visibility
        if (activeDisplay->isWithinFrameBounds(displayX, displayY,
                                              usableAreaAdjustTop, usableAreaAdjustBottom,
                                              usableAreaAdjustLeft, usableAreaAdjustRight)) {
            tft->drawPixel(displayX, displayY, pixelColor);
        }
        
        // Advance to next pixel
        currentCol++;
        if (currentCol >= bitmapWidth) {
            currentCol = 0;
            currentRow++;
            
            // Progress indication every PROGRESS_REPORT_INTERVAL rows
            if (currentRow % PROGRESS_REPORT_INTERVAL == 0 && currentRow < bitmapHeight) {
                float progress = (float)currentRow / bitmapHeight * 100.0f;
                serialPort.print("Progress: ");
                serialPort.print(progress, 1);
                serialPort.print("% (Row ");
                serialPort.print(currentRow);
                serialPort.print("/");
                serialPort.print(bitmapHeight);
                serialPort.println(")");
            }
        }
    }
}

void SerialProtocol::handleEnd() {
    String endCommand = serialPort.readStringUntil('\n');
    endCommand.trim();
    
    if (endCommand == "BMPEnd") {
        // Draw frame if enabled
        if (imageFrameEnabled && activeDisplay) {
            activeDisplay->drawImageFrame(imageFrameColor, imageFrameThickness);
        }
        
        currentState = BITMAP_COMPLETE;
        serialPort.println("COMPLETE");
        serialPort.println("Bitmap display completed successfully!");
    }
}

void SerialProtocol::handleComplete() {
    // Ready for next bitmap - stay in display selected mode
    currentState = WAITING_FOR_START;
    bitmapWidth = 0;
    bitmapHeight = 0;
    currentRow = 0;
    currentCol = 0;
    offsetX = 0;
    offsetY = 0;
    serialPort.println("Ready for next bitmap");
}

bool SerialProtocol::validateDimensions(int width, int height) {
    if (!activeDisplay) {
        sendError("No active display selected");
        return false;
    }
    
    const DisplayConfig& cfg = activeDisplay->getConfig();
    
    // Check for negative or zero dimensions
    if (width <= 0 || height <= 0) {
        sendError("Invalid dimensions: width=" + String(width) + ", height=" + String(height));
        return false;
    }
    
    // Check against maximum allowed dimensions
    if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
        sendError("Dimensions too large: width=" + String(width) + ", height=" + String(height));
        return false;
    }
    
    if (width > cfg.usableWidth) {
        sendError("Width " + String(width) + " exceeds usable width " + String(cfg.usableWidth));
        return false;
    }
    
    if (height > cfg.usableHeight) {
        sendError("Height " + String(height) + " exceeds usable height " + String(cfg.usableHeight));
        return false;
    }
    
    serialPort.print("Dimensions validated: ");
    serialPort.print(width);
    serialPort.print("x");
    serialPort.println(height);
    return true;
}

bool SerialProtocol::calculateOffsets(int bmpWidth, int bmpHeight, int& offsetX, int& offsetY) {
    if (!activeDisplay) {
        return false;
    }
    
    const DisplayConfig& cfg = activeDisplay->getConfig();
    
    // Calculate centering offsets within usable area
    int usableCenterX = cfg.usableX + cfg.usableWidth / 2;
    int usableCenterY = cfg.usableY + cfg.usableHeight / 2;
    int bitmapCenterX = bmpWidth / 2;
    int bitmapCenterY = bmpHeight / 2;
    
    offsetX = usableCenterX - bitmapCenterX;
    offsetY = usableCenterY - bitmapCenterY;
    
    // Verify bounds
    int minX = offsetX;
    int maxX = offsetX + bmpWidth - 1;
    int minY = offsetY;
    int maxY = offsetY + bmpHeight - 1;
    
    if (!activeDisplay->isWithinBounds(minX, minY) || 
        !activeDisplay->isWithinBounds(maxX, maxY)) {
        sendError("Calculated bitmap position exceeds bounds");
        return false;
    }
    
    serialPort.print("Usable center: (");
    serialPort.print(usableCenterX);
    serialPort.print(", ");
    serialPort.print(usableCenterY);
    serialPort.println(")");
    
    serialPort.print("Bitmap center: (");
    serialPort.print(bitmapCenterX);
    serialPort.print(", ");
    serialPort.print(bitmapCenterY);
    serialPort.println(")");
    
    serialPort.print("Centering at offset: (");
    serialPort.print(offsetX);
    serialPort.print(", ");
    serialPort.print(offsetY);
    serialPort.println(")");
    
    serialPort.print("Bitmap will occupy: (");
    serialPort.print(minX);
    serialPort.print(",");
    serialPort.print(minY);
    serialPort.print(") to (");
    serialPort.print(maxX);
    serialPort.print(",");
    serialPort.print(maxY);
    serialPort.println(")");
    
    return true;
}

void SerialProtocol::sendError(const String& message) {
    serialPort.print("ERROR: ");
    serialPort.println(message);
    
    // Display error on active display
    if (activeDisplay && activeDisplay->getTFT()) {
        Adafruit_ST7735* tft = activeDisplay->getTFT();
        tft->fillScreen(ST77XX_RED);
        tft->setTextColor(ST77XX_WHITE);
        tft->setTextSize(1);
        tft->setCursor(5, 10);
        tft->println("ERROR:");
        tft->setCursor(5, 25);
        tft->println(message);
    }
    
    reset();
}

void SerialProtocol::reset() {
    currentState = WAITING_FOR_DISPLAY_SELECT;
    activeDisplay = nullptr;
    bitmapWidth = 0;
    bitmapHeight = 0;
    currentRow = 0;
    currentCol = 0;
    offsetX = 0;
    offsetY = 0;
}

void SerialProtocol::checkTimeout() {
    // Only apply timeout to states where data transmission is in progress
    // Do NOT timeout on WAITING_FOR_DISPLAY_SELECT, WAITING_FOR_START, or BITMAP_COMPLETE
    // This allows users unlimited time to select displays and browse for image files
    if (currentState != WAITING_FOR_DISPLAY_SELECT && 
        currentState != WAITING_FOR_START &&
        currentState != BITMAP_COMPLETE && 
        (millis() - lastActivity > TIMEOUT_MS)) {
        sendError("Timeout waiting for data");
        serialPort.println("Timeout - resetting protocol");
        reset();  // Actually reset the protocol state
        lastActivity = millis();  // Reset timeout counter
    }
}

void SerialProtocol::setImageFrameEnabled(bool enabled, uint16_t color, uint8_t thickness) {
    imageFrameEnabled = enabled;
    imageFrameColor = color;
    imageFrameThickness = thickness;
}
