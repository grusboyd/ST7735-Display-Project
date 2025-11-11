/*
 * ST7735 Bitmap Display Receiver - v3.1 Unified Protocol Architecture
 * Arduino Due program to receive bitmap data and display on multiple ST7735 LCDs
 * 
 * Features:
 * - Multi-display support (all displays initialized at startup)
 * - Test patterns shown on all displays by default
 * - Runtime display selection via serial protocol
 * - Unified protocol with CMD: and DISPLAY: command routing
 * - Single Native USB port (/dev/ttyACM0) for all communications
 * 
 * Configuration:
 * - All displays auto-configured from .config files
 * - Generate header: python3 generate_config_header_multi.py
 * - No firmware recompilation needed to switch displays
 * 
 * Protocol:
 * - CMD: prefix for menu/control commands (see CMD:HELP)
 * - DISPLAY: prefix for bitmap transfer protocol
 * - Responses: OK:<data> or ERROR:<message>
 * 
 * Wiring for ST7735 to Arduino Due:
 * VCC -> 3.3V
 * GND -> GND
 * CS, RST, DC, BL -> Per DisplayConfig.h (from .config files)
 * SDA -> Pin 11 (MOSI)
 * SCK -> Pin 13 (SCK)
 */

#include <Arduino.h>
#include <SPI.h>
#include "DisplayConfig.h"
#include "DisplayManager.h"
#include "SerialProtocol.h"

// Global managers
DisplayManager displayManager;
SerialProtocol* protocol = nullptr;

void setup() {
  // Initialize Native USB port only (Programming Port causes auto-reset)
  // Note: Baud rate is ignored on Native USB but set for consistency
  SerialUSB.begin(2000000);  // 2 Mbps (actual speed determined by USB)
  delay(500);  // Brief delay for stability
  
  SerialUSB.println("\n===========================================");
  SerialUSB.println("ST7735 Multi-Display System v3.1 - Unified Protocol");
  SerialUSB.println("===========================================\n");
  
  // Initialize SPI
  SPI.begin();
  SerialUSB.println("SPI initialized");
  
  // Register all displays from config
  initializeDisplayRegistry(displayManager);
  SerialUSB.print("Registered ");
  SerialUSB.print(displayManager.getDisplayCount());
  SerialUSB.println(" display(s)");
  
  // List registered displays
  displayManager.listDisplays(SerialUSB);
  
  // Initialize all displays
  SerialUSB.println("\nInitializing displays...");
  if (displayManager.initializeAll()) {
    SerialUSB.println("✓ All displays initialized successfully");
  } else {
    SerialUSB.println("⚠ Some displays failed to initialize");
  }
  
  // Show test patterns on all displays
  SerialUSB.println("\nDisplaying test patterns on all screens...");
  displayManager.showAllTestPatterns();
  SerialUSB.println("✓ Test patterns displayed");
  
  // Initialize protocol handler with SerialUSB
  protocol = new SerialProtocol(displayManager, SerialUSB);
  
  SerialUSB.println("\n===========================================");
  SerialUSB.println("System ready!");
  SerialUSB.println("===========================================");
  SerialUSB.println("\nUnified Protocol on Native USB Port");
  SerialUSB.println("Port assignment varies - typically /dev/ttyACM0 or /dev/ttyACM1");
  SerialUSB.println("Use 'ls -la /dev/ttyACM*' to identify ports");
  SerialUSB.println("\nCommands:");
  SerialUSB.println("  CMD:HELP - Show all available commands");
  SerialUSB.println("  CMD:LIST - List displays");
  SerialUSB.println("  DISPLAY:<name> - Select display for bitmap");
  SerialUSB.println();
}

void loop() {
  // Protocol processing handles all commands (CMD: and DISPLAY:)
  if (protocol) {
    protocol->process();
    protocol->checkTimeout();
  }
  
  // Small delay to prevent overwhelming the processor
  delay(1);
}
