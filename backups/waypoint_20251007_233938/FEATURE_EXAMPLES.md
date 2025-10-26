# Adding New Features - Example Guide

This guide demonstrates how to add new features to the ST7735 dual display system using the extensible FeaturePolicy architecture.

## Example: StatusMonitor Feature

Let's create a simple StatusMonitor feature that displays system information on a portion of Display 2.

### Step 1: Create the Feature Class

```cpp
class StatusMonitor : public FeaturePolicy {
private:
    DisplayController* controller;
    unsigned long lastUpdate;
    unsigned long updateInterval;
    bool active;
    
public:
    StatusMonitor(unsigned long interval = 5000) 
        : controller(nullptr), lastUpdate(0), updateInterval(interval), active(true) {}
    
    void initialize(DisplayController* ctrl) override {
        controller = ctrl;
        lastUpdate = millis();
        
        Serial.println("StatusMonitor: Initialized");
        drawInitialStatus();
    }
    
    void update() override {
        if (!active) return;
        
        unsigned long now = millis();
        if (now - lastUpdate >= updateInterval) {
            updateStatus();
            lastUpdate = now;
        }
    }
    
    const char* getName() const override {
        return "StatusMonitor";
    }
    
    bool isActive() const override {
        return active;
    }
    
    void setActive(bool state) {
        active = state;
        if (!active) {
            clearStatusArea();
        }
    }
    
    void setUpdateInterval(unsigned long interval) {
        updateInterval = interval;
    }

private:
    void drawInitialStatus() {
        controller->selectDisplay(1);  // Display 2
        Adafruit_ST7735* display = controller->getDisplay(1);
        
        // Draw status area background (top-left corner)
        display->fillRect(5, 5, 50, 30, ST77XX_BLUE);
        display->drawRect(4, 4, 52, 32, ST77XX_WHITE);
        
        // Initial status text
        display->setTextColor(ST77XX_WHITE);
        display->setTextSize(1);
        display->setCursor(6, 8);
        display->println("STATUS");
        display->setCursor(6, 18);
        display->println("INIT");
    }
    
    void updateStatus() {
        controller->selectDisplay(1);  // Display 2
        Adafruit_ST7735* display = controller->getDisplay(1);
        
        // Clear status text area (keep border)
        display->fillRect(5, 5, 50, 30, ST77XX_BLUE);
        
        // Update status information
        display->setTextColor(ST77XX_WHITE);
        display->setTextSize(1);
        display->setCursor(6, 8);
        display->println("UPTIME");
        
        display->setCursor(6, 18);
        unsigned long uptime = millis() / 1000;
        if (uptime < 100) {
            display->print(uptime);
            display->println("s");
        } else {
            display->print(uptime / 60);
            display->println("m");
        }
        
        // Memory status
        display->setCursor(6, 28);
        display->print("MEM:OK");
    }
    
    void clearStatusArea() {
        controller->selectDisplay(1);  // Display 2
        Adafruit_ST7735* display = controller->getDisplay(1);
        
        // Clear the entire status area
        display->fillRect(4, 4, 52, 32, ST77XX_BLACK);
    }
};
```

### Step 2: Register the Feature

Add this to your main setup code:

```cpp
// Global instances
DisplayController displayController;
FeatureManager featureManager(&displayController);
BitmapReceiver bitmapReceiver;
FrameRenderer frameRenderer;
StatusMonitor statusMonitor(3000);  // Update every 3 seconds

void setup() {
    // ... existing setup code ...
    
    // Add features to the extensible policy system
    featureManager.addFeature(&bitmapReceiver);
    featureManager.addFeature(&frameRenderer);
    featureManager.addFeature(&statusMonitor);  // Add the new feature
    
    // ... rest of setup ...
}
```

### Step 3: Optional Runtime Control

You can add runtime control through serial commands:

```cpp
class SerialCommandHandler : public FeaturePolicy {
private:
    DisplayController* controller;
    FeatureManager* featureManager;
    
public:
    SerialCommandHandler(FeatureManager* fm) 
        : controller(nullptr), featureManager(fm) {}
    
    void initialize(DisplayController* ctrl) override {
        controller = ctrl;
        Serial.println("SerialCommandHandler: Ready for commands");
        Serial.println("Commands: status_on, status_off, status_rate <ms>");
    }
    
    void update() override {
        if (Serial.available()) {
            String command = Serial.readStringUntil('\n');
            command.trim();
            command.toLowerCase();
            
            if (command == "status_on") {
                StatusMonitor* status = (StatusMonitor*)featureManager->getFeature("StatusMonitor");
                if (status) {
                    status->setActive(true);
                    Serial.println("StatusMonitor enabled");
                }
            }
            else if (command == "status_off") {
                StatusMonitor* status = (StatusMonitor*)featureManager->getFeature("StatusMonitor");
                if (status) {
                    status->setActive(false);
                    Serial.println("StatusMonitor disabled");
                }
            }
            else if (command.startsWith("status_rate ")) {
                unsigned long rate = command.substring(12).toInt();
                if (rate >= 1000) {  // Minimum 1 second
                    StatusMonitor* status = (StatusMonitor*)featureManager->getFeature("StatusMonitor");
                    if (status) {
                        status->setUpdateInterval(rate);
                        Serial.println("StatusMonitor rate set to " + String(rate) + "ms");
                    }
                }
            }
        }
    }
    
    const char* getName() const override {
        return "SerialCommandHandler";
    }
    
    bool isActive() const override {
        return true;
    }
};
```

## Example: BlinkingLED Feature

Here's another simple example showing a feature that doesn't use displays but demonstrates the pattern:

```cpp
class BlinkingLED : public FeaturePolicy {
private:
    uint8_t ledPin;
    unsigned long lastBlink;
    unsigned long blinkInterval;
    bool ledState;
    bool active;
    
public:
    BlinkingLED(uint8_t pin, unsigned long interval = 1000) 
        : ledPin(pin), lastBlink(0), blinkInterval(interval), ledState(false), active(true) {}
    
    void initialize(DisplayController* ctrl) override {
        pinMode(ledPin, OUTPUT);
        digitalWrite(ledPin, LOW);
        lastBlink = millis();
        Serial.println("BlinkingLED: Initialized on pin " + String(ledPin));
    }
    
    void update() override {
        if (!active) return;
        
        unsigned long now = millis();
        if (now - lastBlink >= blinkInterval) {
            ledState = !ledState;
            digitalWrite(ledPin, ledState ? HIGH : LOW);
            lastBlink = now;
        }
    }
    
    const char* getName() const override {
        return "BlinkingLED";
    }
    
    bool isActive() const override {
        return active;
    }
    
    void setActive(bool state) {
        active = state;
        if (!active) {
            digitalWrite(ledPin, LOW);
            ledState = false;
        }
    }
    
    void setBlinkRate(unsigned long interval) {
        blinkInterval = interval;
    }
};
```

## Best Practices for Feature Development

### 1. Resource Management
- Always check if resources are available before using them
- Clean up properly when features are disabled
- Don't assume exclusive access to display areas

### 2. Performance Considerations
- Use timing-based updates rather than continuous operations
- Batch display operations when possible
- Minimize Serial.print() calls in tight loops

### 3. Error Handling
```cpp
void update() override {
    if (!controller) {
        Serial.println("FeatureName: ERROR - Controller not initialized");
        return;
    }
    
    if (!isActive()) return;
    
    // Feature logic with error checking
    Adafruit_ST7735* display = controller->getDisplay(displayId);
    if (!display) {
        Serial.println("FeatureName: ERROR - Invalid display ID");
        return;
    }
    
    // Safe operations
}
```

### 4. Configuration Options
- Make features configurable through constructor parameters
- Provide runtime configuration methods when appropriate
- Use reasonable defaults

### 5. Debugging and Logging
- Include feature name in all log messages
- Provide initialization confirmation
- Log significant state changes

## Integration Checklist

When adding a new feature:

- [ ] Feature class inherits from FeaturePolicy
- [ ] All virtual methods implemented
- [ ] Feature registered with FeatureManager
- [ ] Resources properly initialized and cleaned up
- [ ] Error handling implemented
- [ ] Performance considerations addressed
- [ ] Documentation updated
- [ ] Changelog entry added

## Advanced Examples

For more complex features, consider:

1. **Multi-Display Features**: Features that coordinate between multiple displays
2. **Interactive Features**: Features that respond to external input
3. **Data Processing Features**: Features that process and visualize data streams
4. **Communication Features**: Features that handle network or wireless communication

The extensible architecture supports all these patterns while maintaining clean separation of concerns and optimal performance.