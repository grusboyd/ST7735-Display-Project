/*
 * ST7735 Display Calibration Tool
 * Interactive tool to identify display bounds, origin, and usable area
 * Exports calibration data as TOML .config files
 * 
 * TO USE THIS CALIBRATION TOOL:
 * 1. Copy this file to src/main.cpp (backup the original main.cpp first)
 * 2. Build and upload to Arduino Due
 * 3. Use serial monitor at 115200 baud to run calibration commands
 * 4. Use 'bounds' command to set calibration values
 * 5. Use 'export' command to generate .config file
 * 6. Copy/paste output to save as <DeviceName>.config
 * 7. Run: python3 generate_config_header.py --device <DeviceName>
 * 8. Restore the original main.cpp
 * 
 * Default wiring (modify pin definitions below for your setup):
 * VCC -> 3.3V
 * GND -> GND
 * CS  -> Pin 7
 * RST -> Pin 8  
 * DC  -> Pin 10
 * SDA -> Pin 11 (MOSI)
 * SCK -> Pin 13 (SCK)
 * BL  -> Pin 9 (backlight)
 * 
 * Workflow:
 * 1. Run 'frame' to see display boundaries
 * 2. Run 'bounds L,R,T,B' with observed values (e.g., 'bounds 1,158,2,127')
 * 3. Run 'center' to verify center point
 * 4. Run 'export' to generate .config file
 * 5. Copy/paste output and save to file
 */

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>

// ST7735 pin definitions - DueLCD01 configuration
#define TFT_CS     7      // Chip Select
#define TFT_DC     10     // Data/Command select
#define TFT_RST    8      // Reset
#define TFT_BL     9      // Backlight control

// Create ST7735 instance
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// Calibration variables
int currentRotation = 1;  // Default to landscape
int usableOriginX = 0;
int usableOriginY = 0;
int usableWidth = 0;
int usableHeight = 0;

// Function prototypes
void showHelp();
void setRotation(int rotation);
void drawFrame();
void clearScreen();
void drawOriginToCenterLine();
void runCalibrationTest();
void drawUsableCenter();
void processCommand(String command);
void showDisplayInfo();
void waitForKeypress();
void exportConfig();
void setUsableBounds(int left, int right, int top, int bottom);

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  // Initialize backlight control
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);  // Turn on backlight
  
  // Initialize SPI
  SPI.begin();
  
  // Initialize ST7735 display
  tft.initR(INITR_BLACKTAB);   // Initialize ST7735S chip, black tab
  
  // Set default rotation (no auto display)
  currentRotation = 1;
  tft.setRotation(currentRotation);
  
  // Clear screen only
  tft.fillScreen(ST77XX_BLACK);
  
  // Show welcome message and options only
  Serial.println();
  Serial.println("========================================");
  Serial.println("ST7735 Display Calibration Tool v1.0");
  Serial.println("========================================");
  Serial.println();
  Serial.println("Connected! Ready for commands.");
  Serial.println();
  showHelp();
}

void showHelp() {
  Serial.println("Available Commands:");
  Serial.println("  rot0, rot1, rot2, rot3 - Set rotation (0=portrait, 1=landscape, 2=portrait-flipped, 3=landscape-flipped)");
  Serial.println("  frame                  - Draw white frame at display edges (steps through insets)");
  Serial.println("  clear                  - Clear screen to black");
  Serial.println("  cross                  - Draw diagonal line from origin (0,0) to nominal center");
  Serial.println("  test                   - Run complete calibration test (with keypress pauses)");
  Serial.println("  center                 - Draw red cross at calculated usable center");
  Serial.println("  bounds L,R,T,B         - Set usable bounds (e.g., 'bounds 1,158,2,127')");
  Serial.println("  export                 - Export calibration as .config file (copy/paste to save)");
  Serial.println("  info                   - Show current display information");
  Serial.println("  help                   - Show this help");
  Serial.println();
}

void showDisplayInfo() {
  Serial.println("Current Display Information:");
  Serial.println("  Rotation: " + String(currentRotation));
  Serial.println("  Nominal Width: " + String(tft.width()));
  Serial.println("  Nominal Height: " + String(tft.height()));
  if (usableWidth > 0) {
    Serial.println("  Usable Origin: (" + String(usableOriginX) + ", " + String(usableOriginY) + ")");
    Serial.println("  Usable Size: " + String(usableWidth) + " x " + String(usableHeight));
    Serial.println("  Usable Center: (" + String(usableOriginX + usableWidth/2) + ", " + String(usableOriginY + usableHeight/2) + ")");
  }
  Serial.println();
}

void setRotation(int rotation) {
  if (rotation >= 0 && rotation <= 3) {
    currentRotation = rotation;
    tft.setRotation(rotation);
    Serial.println("Rotation set to: " + String(rotation));
    Serial.println("Display size: " + String(tft.width()) + " x " + String(tft.height()));
    
    // Reset usable area when rotation changes
    usableOriginX = 0;
    usableOriginY = 0;
    usableWidth = 0;
    usableHeight = 0;
    
    Serial.println("Use 'cross' command to see origin-to-center line.");
  } else {
    Serial.println("Invalid rotation. Use 0-3.");
  }
}

void clearScreen() {
  tft.fillScreen(ST77XX_BLACK);
  Serial.println("Screen cleared to black using fillScreen().");
}

void drawFrame() {
  Serial.println("Frame test - stepping through insets. Press any key to continue between steps...");
  
  // Step 1: Nominal frame
  clearScreen();
  tft.drawRect(0, 0, tft.width(), tft.height(), ST77XX_WHITE);
  Serial.println("Step 1: White frame at nominal bounds (0,0) to (" + String(tft.width()-1) + "," + String(tft.height()-1) + ")");
  Serial.println("Press any key to continue...");
  waitForKeypress();
  
  // Step 2: Add 1-pixel inset
  tft.drawRect(1, 1, tft.width() - 2, tft.height() - 2, ST77XX_RED);
  Serial.println("Step 2: Added red frame with 1-pixel inset");
  Serial.println("Press any key to continue...");
  waitForKeypress();
  
  // Step 3: Add 2-pixel inset
  tft.drawRect(2, 2, tft.width() - 4, tft.height() - 4, ST77XX_GREEN);
  Serial.println("Step 3: Added green frame with 2-pixel inset");
  Serial.println("Press any key to continue...");
  waitForKeypress();
  
  // Step 4: Add 3-pixel inset
  tft.drawRect(3, 3, tft.width() - 6, tft.height() - 6, ST77XX_BLUE);
  Serial.println("Step 4: Added blue frame with 3-pixel inset");
  Serial.println("Examine which frames are fully visible to determine usable bounds.");
}

void drawOriginToCenterLine() {
  clearScreen();
  
  // Draw coordinate system
  int centerX = tft.width() / 2;
  int centerY = tft.height() / 2;
  
  // Draw line from origin (0,0) to center
  tft.drawLine(0, 0, centerX, centerY, ST77XX_YELLOW);
  
  // Draw axes
  tft.drawLine(0, 0, tft.width() - 1, 0, ST77XX_BLUE);    // X-axis
  tft.drawLine(0, 0, 0, tft.height() - 1, ST77XX_BLUE);   // Y-axis
  
  // Mark origin
  tft.drawPixel(0, 0, ST77XX_WHITE);
  tft.drawPixel(1, 0, ST77XX_WHITE);
  tft.drawPixel(0, 1, ST77XX_WHITE);
  
  // Mark center
  tft.drawPixel(centerX, centerY, ST77XX_RED);
  tft.drawPixel(centerX-1, centerY, ST77XX_RED);
  tft.drawPixel(centerX+1, centerY, ST77XX_RED);
  tft.drawPixel(centerX, centerY-1, ST77XX_RED);
  tft.drawPixel(centerX, centerY+1, ST77XX_RED);
  
  Serial.println("Origin-to-center test:");
  Serial.println("  Origin (0,0): White pixels");
  Serial.println("  Blue lines: X and Y axes from origin");
  Serial.println("  Yellow line: Origin to nominal center");
  Serial.println("  Red cross: Nominal center at (" + String(centerX) + "," + String(centerY) + ")");
  Serial.println("Check if origin and axes are visible.");
}

void runCalibrationTest() {
  Serial.println("Running complete calibration test...");
  Serial.println("Press any key between each step to continue.");
  Serial.println();
  
  // Step 1: Show info
  Serial.println("=== STEP 1: Display Information ===");
  showDisplayInfo();
  Serial.println("Press any key to continue...");
  waitForKeypress();
  
  // Step 2: Clear screen
  Serial.println("=== STEP 2: Clear Screen Test ===");
  clearScreen();
  Serial.println("Press any key to continue...");
  waitForKeypress();
  
  // Step 3: Test rotations
  Serial.println("=== STEP 3: Rotation Test ===");
  for (int rot = 0; rot < 4; rot++) {
    Serial.println("Testing rotation " + String(rot) + "...");
    setRotation(rot);
    Serial.println("Press any key to continue to next rotation...");
    waitForKeypress();
  }
  
  // Step 4: Frame test
  Serial.println("=== STEP 4: Frame Boundary Test ===");
  drawFrame();
  
  // Step 5: Center test
  Serial.println("=== STEP 5: Usable Center Test ===");
  drawUsableCenter();
  
  Serial.println();
  Serial.println("=== CALIBRATION TEST COMPLETE ===");
  Serial.println("Based on your observations, you can determine:");
  Serial.println("  1. Which rotation works best for your setup");
  Serial.println("  2. The actual usable origin coordinates");
  Serial.println("  3. The actual usable display dimensions");
  Serial.println("Use individual commands for fine-tuning.");
}

void drawUsableCenter() {
  if (usableWidth == 0 || usableHeight == 0) {
    Serial.println("Usable area not defined. Please set it first.");
    Serial.println("Example: After determining usable area, manually set:");
    Serial.println("  usableOriginX = 1; usableOriginY = 2;");
    Serial.println("  usableWidth = 158; usableHeight = 126;");
    Serial.println("Then call this function again.");
    
    // For demonstration, use common ST7735 values
    usableOriginX = 1;
    usableOriginY = 2;
    usableWidth = tft.width() - 2;
    usableHeight = tft.height() - 3;
    
    Serial.println("Using estimated values for demonstration:");
    showDisplayInfo();
  }
  
  clearScreen();
  
  // Calculate usable center
  int centerX = usableOriginX + usableWidth / 2;
  int centerY = usableOriginY + usableHeight / 2;
  
  // Draw red cross at usable center
  tft.drawLine(centerX - 5, centerY, centerX + 5, centerY, ST77XX_RED);  // Horizontal
  tft.drawLine(centerX, centerY - 5, centerX, centerY + 5, ST77XX_RED);  // Vertical
  
  // Draw usable area boundary
  tft.drawRect(usableOriginX, usableOriginY, usableWidth, usableHeight, ST77XX_GREEN);
  
  Serial.println("Red cross drawn at usable center: (" + String(centerX) + "," + String(centerY) + ")");
  Serial.println("Green rectangle shows usable area boundary.");
}

void waitForKeypress() {
  // Clear any pending input
  while (Serial.available()) {
    Serial.read();
  }
  
  // Wait for any key
  while (!Serial.available()) {
    delay(50);
  }
  
  // Read the key (but don't process as command)
  Serial.readString();
  Serial.println();
}

void setUsableBounds(int left, int right, int top, int bottom) {
  usableOriginX = left;
  usableOriginY = top;
  usableWidth = right - left + 1;
  usableHeight = bottom - top + 1;
  
  Serial.println("Usable bounds set:");
  Serial.println("  Left: " + String(left) + ", Right: " + String(right));
  Serial.println("  Top: " + String(top) + ", Bottom: " + String(bottom));
  Serial.println("  Usable area: " + String(usableWidth) + "x" + String(usableHeight));
  Serial.println("  Center: (" + String(left + usableWidth/2) + ", " + String(top + usableHeight/2) + ")");
}

void exportConfig() {
  if (usableWidth == 0 || usableHeight == 0) {
    Serial.println("Error: Usable bounds not set. Use 'bounds' command first.");
    Serial.println("Example: bounds 1,158,2,127");
    return;
  }
  
  // Determine orientation string
  String orientation = "landscape";
  if (currentRotation == 0) orientation = "portrait";
  else if (currentRotation == 1) orientation = "landscape";
  else if (currentRotation == 2) orientation = "reverse_portrait";
  else if (currentRotation == 3) orientation = "reverse_landscape";
  
  // Calculate center
  int centerX = usableOriginX + usableWidth / 2;
  int centerY = usableOriginY + usableHeight / 2;
  
  Serial.println();
  Serial.println("========== BEGIN CONFIG FILE ==========");
  Serial.println("# ST7735 Display Configuration");
  Serial.println("# Format: TOML v1.0.0");
  Serial.println("# Generated by cal_lcd.cpp");
  Serial.println();
  Serial.println("[device]");
  Serial.println("name = \"DueLCD_NEW\"  # TODO: Change to unique device name");
  Serial.println("manufacturer = \"Unknown\"  # TODO: Set manufacturer");
  Serial.println("model = \"ST7735\"  # TODO: Set model");
  Serial.println("published_resolution = [" + String(tft.width()) + ", " + String(tft.height()) + "]");
  Serial.println();
  Serial.println("[pinout]");
  Serial.println("# Arduino Due pin assignments");
  Serial.println("rst = " + String(TFT_RST));
  Serial.println("dc = " + String(TFT_DC));
  Serial.println("cs = " + String(TFT_CS));
  Serial.println("bl = " + String(TFT_BL));
  Serial.println();
  Serial.println("[calibration]");
  Serial.println("orientation = \"" + orientation + "\"");
  Serial.println("# Usable area bounds (0-indexed, inclusive)");
  Serial.println("left = " + String(usableOriginX));
  Serial.println("right = " + String(usableOriginX + usableWidth - 1));
  Serial.println("top = " + String(usableOriginY));
  Serial.println("bottom = " + String(usableOriginY + usableHeight - 1));
  Serial.println("# Calculated center point");
  Serial.println("center = [" + String(centerX) + ", " + String(centerY) + "]");
  Serial.println("=========== END CONFIG FILE ===========");
  Serial.println();
  Serial.println("Copy the text between BEGIN/END and save as <DeviceName>.config");
  Serial.println("Then run: python3 generate_config_header.py --device <DeviceName>");
}

void processCommand(String command) {
  command.trim();
  String commandLower = command;
  commandLower.toLowerCase();
  
  bool showHelpAfter = true;  // Show help after most commands
  
  if (commandLower == "rot0") {
    setRotation(0);
  } else if (commandLower == "rot1") {
    setRotation(1);
  } else if (commandLower == "rot2") {
    setRotation(2);
  } else if (commandLower == "rot3") {
    setRotation(3);
  } else if (commandLower == "frame") {
    drawFrame();
  } else if (commandLower == "clear") {
    clearScreen();
  } else if (commandLower == "cross") {
    drawOriginToCenterLine();
  } else if (commandLower == "test") {
    runCalibrationTest();
    showHelpAfter = false;  // Don't show help after test (it shows its own conclusion)
  } else if (commandLower == "center") {
    drawUsableCenter();
  } else if (commandLower.startsWith("bounds ")) {
    // Parse bounds command: "bounds L,R,T,B"
    String params = command.substring(7);
    int commaPos1 = params.indexOf(',');
    int commaPos2 = params.indexOf(',', commaPos1 + 1);
    int commaPos3 = params.indexOf(',', commaPos2 + 1);
    
    if (commaPos1 > 0 && commaPos2 > 0 && commaPos3 > 0) {
      int left = params.substring(0, commaPos1).toInt();
      int right = params.substring(commaPos1 + 1, commaPos2).toInt();
      int top = params.substring(commaPos2 + 1, commaPos3).toInt();
      int bottom = params.substring(commaPos3 + 1).toInt();
      setUsableBounds(left, right, top, bottom);
    } else {
      Serial.println("Error: Invalid bounds format. Use: bounds L,R,T,B");
      Serial.println("Example: bounds 1,158,2,127");
    }
  } else if (commandLower == "export") {
    exportConfig();
    showHelpAfter = false;  // Export shows its own instructions
  } else if (commandLower == "info") {
    showDisplayInfo();
  } else if (commandLower == "help") {
    showHelp();
    showHelpAfter = false;  // Already showed help
  } else if (command.length() > 0) {
    Serial.println("Unknown command: " + command);
    Serial.println("Type 'help' for available commands.");
    showHelpAfter = false;
  } else {
    showHelpAfter = false;  // Empty command, don't show help
  }
  
  // Show help menu after command completion (except for test and help commands)
  if (showHelpAfter) {
    Serial.println();
    Serial.println("--- Command completed. Available commands: ---");
    showHelp();
  }
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
  
  delay(10);  // Small delay
}