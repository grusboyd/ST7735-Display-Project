/*
 * DisplayManager.h
 * Multi-display management for ST7735 displays
 * 
 * Manages multiple ST7735 display instances with:
 * - Individual display initialization
 * - Test pattern generation
 * - Display selection and lookup
 * - Coordinated operations across displays
 */

#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>

// Display configuration structure
struct DisplayConfig {
    const char* name;
    const char* manufacturer;
    const char* model;
    
    // Pin assignments
    uint8_t cs;
    uint8_t dc;
    uint8_t rst;
    uint8_t bl;
    
    // Display dimensions
    uint16_t width;
    uint16_t height;
    uint8_t rotation;
    
    // Calibrated usable area
    uint16_t usableX;
    uint16_t usableY;
    uint16_t usableWidth;
    uint16_t usableHeight;
    
    // Center point
    uint16_t centerX;
    uint16_t centerY;
};

// Display instance wrapper
class DisplayInstance {
public:
    DisplayInstance(const DisplayConfig& config);
    ~DisplayInstance();
    
    bool initialize();
    void showTestPattern();
    void clear();
    void setBacklight(bool on);
    
    // Getters
    const char* getName() const { return config.name; }
    const DisplayConfig& getConfig() const { return config; }
    Adafruit_ST7735* getTFT() { return tft; }
    
    // Drawing helpers
    void drawCalibrationFrame(int8_t adjustTop = 0, int8_t adjustBottom = 0,
                             int8_t adjustLeft = 0, int8_t adjustRight = 0,
                             uint16_t frameColor = ST77XX_WHITE, uint8_t frameThickness = 1);
    void drawColorBars();
    void drawDeviceInfo();
    bool isWithinBounds(int x, int y) const;
    bool isWithinFrameBounds(int x, int y, 
                            int8_t adjustTop = 0, int8_t adjustBottom = 0,
                            int8_t adjustLeft = 0, int8_t adjustRight = 0) const;
    
    // Image frame support
    void drawImageFrame(uint16_t color = ST77XX_WHITE, uint8_t thickness = 1, 
                       int8_t adjustTop = 0, int8_t adjustBottom = 0, 
                       int8_t adjustLeft = 0, int8_t adjustRight = 0);
    void clearImageFrame();
    void enableImageFrame(bool enable, uint16_t color = ST77XX_WHITE, uint8_t thickness = 1,
                         int8_t adjustTop = 0, int8_t adjustBottom = 0,
                         int8_t adjustLeft = 0, int8_t adjustRight = 0);
    bool isImageFrameEnabled() const { return imageFrameEnabled; }
    
private:
    // Image frame state
    bool imageFrameEnabled;
    uint16_t imageFrameColor;
    uint8_t imageFrameThickness;
    uint16_t* frameBuffer;  // Stores pixels under frame for restoration
    bool frameBufferAllocated;
    DisplayConfig config;
    Adafruit_ST7735* tft;
    bool initialized;
};

// Main display manager class
class DisplayManager {
public:
    DisplayManager();
    ~DisplayManager();
    
    // Setup
    bool addDisplay(const DisplayConfig& config);
    bool initializeAll();
    void showAllTestPatterns();
    
    // Display selection
    DisplayInstance* getDisplay(const char* name);
    DisplayInstance* getDisplay(uint8_t index);
    uint8_t getDisplayCount() const { return displayCount; }
    
    // Utility
    void listDisplays(Stream& serial);
    
private:
    static const uint8_t MAX_DISPLAYS = 8;
    DisplayInstance* displays[MAX_DISPLAYS];
    uint8_t displayCount;
};

#endif // DISPLAY_MANAGER_H
