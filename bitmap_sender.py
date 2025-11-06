#!/usr/bin/env python3
"""
Bitmap Sender for ST7735 Display
Raspberry Pi program to send bitmap images to Arduino Due via serial
Compatible with the ST7735 bitmap display receiver protocol

Requirements:
- Python 3.6+
- pyserial: pip install pyserial
- Pillow (PIL): pip install Pillow

Usage:
    python3 bitmap_sender.py <image_file> [serial_port]
    
Example:
    python3 bitmap_sender.py image.jpg /dev/ttyACM1
"""

import sys
import time
import argparse
from pathlib import Path
import serial
from PIL import Image, ImageOps
import struct

# Import config loader from st7735_tools
try:
    from st7735_tools.config_loader import load_display_config, find_config_files, get_config_by_device_name
except ImportError:
    print("Error: st7735_tools module not found. Make sure config_loader.py exists.")
    sys.exit(1)

# Default display configuration (fallback if no config specified)
DISPLAY_WIDTH = 158   # Usable width (calibrated)
DISPLAY_HEIGHT = 126  # Usable height (calibrated)
SERIAL_BAUDRATE = 115200
TIMEOUT_SECONDS = 10

class BitmapSender:
    def __init__(self, serial_port='/dev/ttyACM2', baudrate=SERIAL_BAUDRATE, display_config=None):
        """
        Initialize the bitmap sender
        
        Args:
            serial_port (str): Serial port path (e.g., '/dev/ttyACM0')
            baudrate (int): Serial communication baud rate
            display_config: DisplayConfig object (optional, uses defaults if None)
        """
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.connection = None
        self.display_config = display_config
        
        # Set display dimensions from config or use defaults
        if display_config:
            self.display_width = display_config.usable_width
            self.display_height = display_config.usable_height
            print(f"Using config: {display_config.name} ({display_config.usable_width}x{display_config.usable_height})")
        else:
            self.display_width = DISPLAY_WIDTH
            self.display_height = DISPLAY_HEIGHT
            print(f"Using default dimensions: {self.display_width}x{self.display_height}")
        
    def connect(self):
        """Establish serial connection to Arduino Due"""
        try:
            print(f"Connecting to Arduino Due on {self.serial_port}...")
            self.connection = serial.Serial(
                self.serial_port, 
                self.baudrate, 
                timeout=TIMEOUT_SECONDS,
                write_timeout=TIMEOUT_SECONDS
            )
            
            # Wait for Arduino to initialize
            print("Waiting for Arduino to initialize...")
            time.sleep(2)
            
            # Read any startup messages
            while self.connection.in_waiting > 0:
                line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Arduino: {line}")
            
            print("Connection established!")
            return True
            
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            print(f"Make sure Arduino Due is connected to {self.serial_port}")
            print("Common serial ports on Raspberry Pi:")
            print("  /dev/ttyACM0 (Arduino Due)")
            print("  /dev/ttyUSB0 (USB-Serial adapter)")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Disconnected from Arduino")
    
    def wait_for_response(self, expected_response=None, timeout=5):
        """
        Wait for response from Arduino
        
        Args:
            expected_response (str): Expected response string (optional)
            timeout (int): Timeout in seconds
            
        Returns:
            str: Response received, or None if timeout
        """
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < timeout:
            if self.connection.in_waiting > 0:
                try:
                    line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"Arduino: {line}")
                        response = line
                        
                        if expected_response is None or expected_response in line:
                            return response
                except:
                    pass
            time.sleep(0.01)
        
        return None
    
    def rgb888_to_rgb565(self, r, g, b):
        """
        Convert RGB888 (24-bit) to RGB565 (16-bit)
        
        Args:
            r, g, b (int): RGB values (0-255)
            
        Returns:
            int: RGB565 value (16-bit)
        """
        # Convert 8-bit values to 5-bit (R), 6-bit (G), 5-bit (B)
        r5 = (r >> 3) & 0x1F
        g6 = (g >> 2) & 0x3F  
        b5 = (b >> 3) & 0x1F
        
        # Pack into 16-bit value: RRRRRGGGGGGBBBBB
        rgb565 = (r5 << 11) | (g6 << 5) | b5
        return rgb565
    
    def prepare_image(self, image_path):
        """
        Load and prepare image for display
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            tuple: (width, height, pixel_data) or None if error
        """
        try:
            print(f"Loading image: {image_path}")
            
            # Open and convert image
            with Image.open(image_path) as img:
                print(f"Original image size: {img.size}")
                print(f"Original image mode: {img.mode}")
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    print("Converting image to RGB...")
                    img = img.convert('RGB')
                
                # Calculate scaling to fit display while maintaining aspect ratio
                # No rotation needed - display rotation will handle orientation
                img_width, img_height = img.size
                
                scale_x = self.display_width / img_width
                scale_y = self.display_height / img_height
                
                # Try to fill at least one dimension completely
                scale_max = max(scale_x, scale_y)
                scale_min = min(scale_x, scale_y)
                
                # Calculate what the size would be with max scale
                test_width = int(img_width * scale_max)
                test_height = int(img_height * scale_max)
                
                # If max scale fits within display bounds, use it; otherwise fall back to min scale
                if test_width <= self.display_width and test_height <= self.display_height:
                    scale = scale_max
                    print(f"Using max scale to fill dimension: {scale:.3f}")
                else:
                    scale = scale_min
                    print(f"Using min scale to fit display: {scale:.3f}")
                
                # Calculate final size
                final_width = int(img_width * scale)
                final_height = int(img_height * scale)
                
                print(f"Scaling to: {final_width}x{final_height}")
                
                # Resize image (no rotation needed)
                img_resized = img.resize((final_width, final_height), Image.Resampling.LANCZOS)
                
                new_width, new_height = img_resized.size
                print(f"Final size: ({new_width}, {new_height})")
                
                # Update dimensions after rotation
                new_width, new_height = img_resized.size
                
                # Final bounds check and crop if necessary
                if new_width > self.display_width or new_height > self.display_height:
                    print(f"Cropping to fit display: {self.display_width}x{self.display_height}")
                    # Calculate crop box to center the image
                    left = max(0, (new_width - self.display_width) // 2)
                    top = max(0, (new_height - self.display_height) // 2)
                    right = left + min(new_width, self.display_width)
                    bottom = top + min(new_height, self.display_height)
                    
                    img_resized = img_resized.crop((left, top, right, bottom))
                    new_width, new_height = img_resized.size
                    print(f"Final cropped size: {new_width}x{new_height}")
                
                # Convert to RGB565 pixel data
                print("Converting to RGB565 format...")
                pixel_data = []
                
                for y in range(new_height):
                    for x in range(new_width):
                        r, g, b = img_resized.getpixel((x, y))
                        rgb565 = self.rgb888_to_rgb565(r, g, b)
                        
                        # Pack as big-endian 16-bit value
                        pixel_data.append(struct.pack('>H', rgb565))
                
                print(f"Prepared {len(pixel_data)} pixels")
                return new_width, new_height, pixel_data
                
        except Exception as e:
            print(f"Error preparing image: {e}")
            return None
    
    def send_bitmap(self, image_path):
        """
        Send bitmap to Arduino Due
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.connection.is_open:
            print("Error: Not connected to Arduino")
            return False
        
        # Prepare image
        image_data = self.prepare_image(image_path)
        if not image_data:
            return False
        
        width, height, pixel_data = image_data
        
        try:
            print("\n=== Starting bitmap transmission ===")
            
            # Step 1: Send start marker
            print("Sending start marker...")
            self.connection.write(b"BMPStart\n")
            self.connection.flush()
            
            # Step 2: Send dimensions
            print(f"Sending dimensions: {width}x{height}")
            size_command = f"SIZE:{width},{height}\n"
            self.connection.write(size_command.encode('utf-8'))
            self.connection.flush()
            
            # Wait for READY response
            response = self.wait_for_response("READY", timeout=5)
            if not response or "READY" not in response:
                print("Error: Arduino did not confirm ready state")
                return False
            
            # Give Arduino a moment to prepare for data reception
            time.sleep(0.1)
            
            # Step 3: Send pixel data
            print(f"Sending {len(pixel_data)} pixels...")
            bytes_sent = 0
            
            # Send pixels in smaller chunks to prevent buffer overflow
            chunk_size = 50  # Send 50 pixels at a time
            for chunk_start in range(0, len(pixel_data), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(pixel_data))
                
                # Send chunk of pixels
                for i in range(chunk_start, chunk_end):
                    self.connection.write(pixel_data[i])
                    bytes_sent += 2
                
                # Flush after each chunk
                self.connection.flush()
                
                # Progress indication
                if (chunk_end) % 1000 == 0 or chunk_end == len(pixel_data):
                    progress = chunk_end / len(pixel_data) * 100
                    print(f"Progress: {progress:.1f}% ({chunk_end}/{len(pixel_data)} pixels, {bytes_sent} bytes)")
                
                # Small delay between chunks to allow Arduino to process
                time.sleep(0.01)
            
            print(f"Pixel data sent: {bytes_sent} bytes")
            
            # Step 4: Send end marker
            print("Sending end marker...")
            self.connection.write(b"BMPEnd\n")
            self.connection.flush()
            
            # Wait for completion confirmation
            response = self.wait_for_response("COMPLETE", timeout=10)
            if response and "COMPLETE" in response:
                print("✓ Bitmap transmission completed successfully!")
                return True
            else:
                print("Warning: Did not receive completion confirmation")
                return True  # Still consider it successful
                
        except Exception as e:
            print(f"Error during transmission: {e}")
            return False
    
    def send_test_pattern(self):
        """Send a test pattern to verify connection"""
        print("Sending test pattern...")
        
        # Create a simple test pattern
        width, height = 50, 40
        pixel_data = []
        
        for y in range(height):
            for x in range(width):
                # Create a simple gradient pattern
                r = (x * 255) // width
                g = (y * 255) // height
                b = 128
                
                rgb565 = self.rgb888_to_rgb565(r, g, b)
                pixel_data.append(struct.pack('>H', rgb565))
        
        try:
            # Send start marker
            self.connection.write(b"BMPStart\n")
            self.connection.flush()
            
            # Send dimensions
            size_command = f"SIZE:{width},{height}\n"
            self.connection.write(size_command.encode('utf-8'))
            self.connection.flush()
            
            # Wait for ready
            response = self.wait_for_response("READY", timeout=5)
            if not response or "READY" not in response:
                print("Error: Arduino not ready for test pattern")
                return False
            
            # Send pixels
            for pixel_bytes in pixel_data:
                self.connection.write(pixel_bytes)
            self.connection.flush()
            
            # Send end marker
            self.connection.write(b"BMPEnd\n")
            self.connection.flush()
            
            print("Test pattern sent successfully!")
            return True
            
        except Exception as e:
            print(f"Error sending test pattern: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Send bitmap images to Arduino Due ST7735 display",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 bitmap_sender.py image.jpg
  python3 bitmap_sender.py photo.png /dev/ttyACM0
  python3 bitmap_sender.py --device DueLCD01 image.jpg
  python3 bitmap_sender.py --config DueLCD02.config photo.png
  python3 bitmap_sender.py --test-pattern /dev/ttyUSB0
  python3 bitmap_sender.py --list-configs
        """
    )
    
    parser.add_argument('image_file', nargs='?', help='Path to image file')
    parser.add_argument('serial_port', nargs='?', default='/dev/ttyACM2', 
                       help='Serial port (default: /dev/ttyACM2 - Native USB port)')
    parser.add_argument('--test-pattern', action='store_true',
                       help='Send a test pattern instead of an image')
    parser.add_argument('--list-ports', action='store_true',
                       help='List available serial ports')
    parser.add_argument('--device', '-d', type=str,
                       help='Device name (e.g., DueLCD01). Auto-loads config file.')
    parser.add_argument('--config', '-c', type=str,
                       help='Path to device config file (e.g., DueLCD01.config)')
    parser.add_argument('--list-configs', action='store_true',
                       help='List available device configurations')
    
    args = parser.parse_args()
    
    # List available configs
    if args.list_configs:
        print("Searching for display configuration files...")
        configs = find_config_files()
        if configs:
            print(f"Found {len(configs)} device configuration(s):")
            for device_name, config_path in configs.items():
                config = load_display_config(str(config_path))
                print(f"  {device_name}: {config_path}")
                print(f"    Resolution: {config.usable_width}x{config.usable_height} ({config.orientation})")
                print(f"    Pins: CS={config.pins['cs']}, DC={config.pins['dc']}, RST={config.pins['rst']}")
        else:
            print("No configuration files found.")
        return 0
    
    # List available ports
    if args.list_ports:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        print("Available serial ports:")
        for port in ports:
            print(f"  {port.device} - {port.description}")
        return 0
    
    # Load display configuration
    display_config = None
    if args.config:
        # Load specific config file
        try:
            print(f"Loading config from: {args.config}")
            display_config = load_display_config(args.config)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return 1
    elif args.device:
        # Load config by device name
        print(f"Looking for device: {args.device}")
        display_config = get_config_by_device_name(args.device)
        if not display_config:
            print(f"Error: No configuration found for device '{args.device}'")
            print("Use --list-configs to see available devices")
            return 1
    
    # Validate arguments
    if not args.test_pattern and not args.image_file:
        print("Error: Please specify an image file or use --test-pattern")
        parser.print_help()
        return 1
    
    if args.image_file and not Path(args.image_file).exists():
        print(f"Error: Image file '{args.image_file}' not found")
        return 1
    
    # Create bitmap sender with optional display config
    sender = BitmapSender(args.serial_port, display_config=display_config)
    
    try:
        # Connect to Arduino
        if not sender.connect():
            return 1
        
        # Send test pattern or image
        if args.test_pattern:
            success = sender.send_test_pattern()
        else:
            success = sender.send_bitmap(args.image_file)
        
        if success:
            print("\n✓ Operation completed successfully!")
            return 0
        else:
            print("\n✗ Operation failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        sender.disconnect()

if __name__ == "__main__":
    sys.exit(main())