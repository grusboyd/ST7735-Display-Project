# Future Enhancements

## Hardware Read Capability (MISO-Connected Displays)

### Current Status
- Project displays lack MISO connectivity
- Current config system is visual calibration-based (hardware-agnostic)
- Works perfectly without hardware reads

### When MISO-Capable Displays Available

#### 1. Python Module Extension (st7735_tools/hardware_reader.py)
```python
def read_display_info_from_hardware(serial_port):
    """
    Query display via SPI read commands
    
    ST7735 Read Commands:
    - 0x04: Read Display ID
    - 0x09: Read Display Status
    - 0x0A: Read Display Power Mode
    - 0x0B: Read Display MADCTL (rotation/mirroring)
    - 0x0C: Read Display Pixel Format
    - 0x0D: Read Display Image Mode
    - 0x0E: Read Display Signal Mode
    
    Returns:
        dict: {
            'chip_id': str,
            'madctl': hex,
            'pixel_format': str,
            'power_mode': str
        }
    """
    pass
```

#### 2. Arduino Tool Enhancement (tools/cal_lcd.cpp)
```cpp
void readDisplayInfo() {
    // SPI read implementation
    uint8_t id1, id2, id3;
    
    // Read Display ID (0x04)
    digitalWrite(TFT_DC, LOW);  // Command mode
    SPI.transfer(0x04);
    digitalWrite(TFT_DC, HIGH); // Data mode
    id1 = SPI.transfer(0x00);   // Dummy read
    id2 = SPI.transfer(0x00);
    id3 = SPI.transfer(0x00);
    
    SerialUSB.print("Chip ID: 0x");
    SerialUSB.print(id1, HEX);
    SerialUSB.print(id2, HEX);
    SerialUSB.println(id3, HEX);
    
    // Read MADCTL (0x0B)
    // Read other registers...
}

// New command: 'readinfo' or 'hwinfo'
```

#### 3. Optional Config File Section
```toml
[hardware_readback]
# Optional: Hardware-reported information (supplementary)
chip_id = "0x7C89F0"
madctl_register = "0x48"
pixel_format = "RGB565"
verified_date = "2025-11-06"
notes = "Hardware info matches visual calibration"
```

#### 4. Auto-Detection Script (optional)
```python
# tools/auto_detect_display.py
def auto_detect_and_suggest():
    """
    1. Read chip ID from hardware
    2. Look up in known display database
    3. Suggest starting calibration values
    4. Still require visual calibration (hardware can lie about usable area)
    """
    pass
```

### Design Philosophy
- Hardware reads are **supplementary validation**, not required
- Visual calibration remains **source of truth**
- Config system works with or without MISO
- Hardware info adds confidence but doesn't replace empirical testing

### Benefits When Implemented
- ✅ Verify chip ID matches expected controller
- ✅ Confirm current rotation register state
- ✅ Detect pixel format mismatches
- ✅ Quick diagnostic for display issues
- ✅ Database of known chip IDs for reference

### Implementation Checklist
When MISO-capable displays arrive:
- [ ] Test MISO connectivity with simple SPI read
- [ ] Add `readDisplayInfo()` to cal_lcd.cpp
- [ ] Add `read_display_info_from_hardware()` to Python tools
- [ ] Create chip ID database/reference
- [ ] Add `[hardware_readback]` section to config template
- [ ] Document SPI read command sequences
- [ ] Add `--verify-hardware` flag to config tools
- [ ] Update CALIBRATION_GUIDE.md with hardware read workflow

### Hardware Requirements
- Display breakout with MISO pin exposed and wired
- 4-wire SPI connection (MOSI, MISO, SCK, CS)
- ST7735 controller (or compatible) with read commands enabled

### Notes
- Typical cheap ST7735 breakouts don't wire MISO (write-only)
- Adafruit library doesn't implement read functions by default
- ST7735 cannot read pixel data from framebuffer
- Read commands mainly return register states, not display characteristics

### Related Files
- `st7735_tools/config_loader.py` - extend with hardware read integration
- `tools/cal_lcd.cpp` - add SPI read commands
- `generate_config_header.py` - optionally include hardware info in header
- `display_config_template.toml` - add [hardware_readback] section

### References
- ST7735 Datasheet: Read commands section
- SPI protocol: Command/data mode switching for reads
- Arduino Due SPI library: transfer() for bidirectional communication
