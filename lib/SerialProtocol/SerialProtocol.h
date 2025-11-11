/*
 * SerialProtocol.h
 * Unified protocol with command routing and bitmap transmission
 * 
 * Protocol supports two command prefixes:
 * 
 * CMD: - Menu/control commands (line-terminated)
 *   CMD:LIST - List all displays
 *   CMD:INFO - Show active display info
 *   CMD:TEST - Test active display
 *   CMD:TEST_ALL - Test all displays
 *   CMD:FRAME_ON - Enable frame
 *   CMD:FRAME_OFF - Disable frame
 *   CMD:FRAME_COLOR:value - Set frame color (0-65535)
 *   CMD:FRAME_THICKNESS:value - Set frame thickness (1-10)
 *   CMD:HELP - Show command help
 *   Responses: OK:<data> or ERROR:<message>
 * 
 * DISPLAY: - Bitmap protocol (existing)
 * 1. Client: "DISPLAY:<device_name>"  -> Select target display
 * 2. Arduino: "DISPLAY_READY" or "DISPLAY_ERROR"
 * 3. Client: "BMPStart"
 * 4. Arduino: "Start marker received"
 * 5. Client: "SIZE:width,height"
 * 6. Arduino: "READY" (after validation)
 * 7. Client: Raw pixel data (RGB565, 2 bytes per pixel)
 * 8. Arduino: Progress updates
 * 9. Client: "BMPEnd"
 * 10. Arduino: "COMPLETE"
 */

#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>
#include "DisplayManager.h"

// Protocol states
enum ProtocolState {
    WAITING_FOR_DISPLAY_SELECT,
    WAITING_FOR_START,
    WAITING_FOR_SIZE,
    RECEIVING_DATA,
    WAITING_FOR_END,
    BITMAP_COMPLETE
};

// Protocol handler class
class SerialProtocol {
public:
    SerialProtocol(DisplayManager& displayMgr, Stream& serial);
    
    // Main processing
    void process();
    void checkTimeout();
    void reset();
    
    // State queries
    ProtocolState getState() const { return currentState; }
    DisplayInstance* getActiveDisplay() const { return activeDisplay; }
    
    // Frame control
    void setImageFrameEnabled(bool enabled, uint16_t color = ST77XX_WHITE, uint8_t thickness = 1);
    bool getImageFrameEnabled() const { return imageFrameEnabled; }
    
private:
    // Protocol constants
    static const unsigned long TIMEOUT_MS = 15000;         // 15 second timeout
    static const unsigned long DISPLAY_SELECT_TIMEOUT = 3000;  // 3 second timeout for display selection
    static const unsigned long READY_TIMEOUT = 5000;       // 5 second timeout for READY response
    static const int MAX_DIMENSION = 1000;                 // Maximum bitmap dimension
    static const int PROGRESS_REPORT_INTERVAL = 10;        // Report progress every N rows
    
    DisplayManager& displayManager;
    Stream& serialPort;
    
    // State
    ProtocolState currentState;
    DisplayInstance* activeDisplay;
    
    // Bitmap reception state
    int bitmapWidth;
    int bitmapHeight;
    int currentRow;
    int currentCol;
    int offsetX;
    int offsetY;
    
    // Timeout tracking
    unsigned long lastActivity;
    
    // Image frame settings
    bool imageFrameEnabled;
    uint16_t imageFrameColor;
    uint8_t imageFrameThickness;
    
    // Calibration usable area adjustments (relative to config values)
    int8_t usableAreaAdjustTop;
    int8_t usableAreaAdjustBottom;
    int8_t usableAreaAdjustLeft;
    int8_t usableAreaAdjustRight;
    
    // Protocol handlers
    void handleDisplaySelect();
    void handleMenuCommand(const String& command);
    void handleStart();
    void handleSize();
    void handleDataReception();
    void handleEnd();
    void handleComplete();
    
    // Validation
    bool validateDimensions(int width, int height);
    bool calculateOffsets(int bmpWidth, int bmpHeight, int& offsetX, int& offsetY);
    
    // Error handling
    void sendError(const String& message);
};

#endif // SERIAL_PROTOCOL_H
