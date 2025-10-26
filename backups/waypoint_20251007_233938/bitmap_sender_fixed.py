#!/usr/bin/env python3
"""
ST7735 Dual Display Project - Bitmap Sender
CORRECTED VERSION - Compatible with dual display Arduino firmware

Properly sends bitmap data using the Arduino's expected protocol:
1. BMPStart
2. SIZE:width,height  
3. Pixel data (RGB565, big-endian)
4. BMPEnd

This version is aware of the dual display system and won't interfere 
with Display 2 (clock) operations.
"""

import sys
import os
from PIL import Image
import serial
import time

# Display 1 specifications (bitmap display)
DISPLAY1_WIDTH = 158
DISPLAY1_HEIGHT = 126

def rgb565_convert(r, g, b):
    """Convert RGB888 to RGB565 format"""
    r = (r >> 3) & 0x1F
    g = (g >> 2) & 0x3F  
    b = (b >> 3) & 0x1F
    return (r << 11) | (g << 5) | b

def process_image_for_display1(image_path):
    """Process image specifically for Display 1 (bitmap display)"""
    try:
        img = Image.open(image_path)
        print(f"Original image size: {img.size}")
        print(f"Original image mode: {img.mode}")
        
        # Convert to RGB if needed
        if img.mode == 'RGBA':
            print("Converting image to RGB...")
            # Create white background and paste RGBA image
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate scaling to fit display while maintaining aspect ratio
        img_width, img_height = img.size
        scale_x = DISPLAY1_WIDTH / img_width
        scale_y = DISPLAY1_HEIGHT / img_height
        scale = min(scale_x, scale_y)  # Use smaller scale to fit within display
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        print(f"Using min scale to fit display: {scale:.3f}")
        print(f"Scaling to: {new_width}x{new_height}")
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f"Final size: {img.size}")
        
        # Convert to RGB565 format
        print("Converting to RGB565 format...")
        pixel_data = []
        pixels = img.load()
        
        for y in range(new_height):
            for x in range(new_width):
                r, g, b = pixels[x, y]
                rgb565 = rgb565_convert(r, g, b)
                # Send as big-endian 16-bit value (Arduino expects this format)
                pixel_data.append((rgb565 >> 8) & 0xFF)  # High byte first
                pixel_data.append(rgb565 & 0xFF)         # Low byte second
        
        print(f"Prepared {len(pixel_data)//2} pixels")
        return pixel_data, new_width, new_height
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, 0, 0

def send_to_arduino_dual_display(pixel_data, width, height, port='/dev/ttyACM0', baudrate=115200):
    """Send bitmap to Arduino using dual display compatible protocol"""
    try:
        print(f"Connecting to Arduino Due on {port}...")
        
        with serial.Serial(port, baudrate, timeout=10) as ser:
            print("Waiting for Arduino to initialize...")
            time.sleep(3)  # Give Arduino time to boot
            
            # Wait for Arduino ready message or timeout
            start_time = time.time()
            arduino_ready = False
            while time.time() - start_time < 10:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"Arduino: {line}")
                        if "Ready to receive" in line or "READY" in line:
                            arduino_ready = True
                            break
                time.sleep(0.1)
            
            if arduino_ready:
                print("Connection established!")
            else:
                print("Arduino response timeout, continuing anyway...")
            
            # Load image info
            print(f"Loading image: {sys.argv[1] if len(sys.argv) > 1 else 'N/A'}")
            print(f"Prepared {len(pixel_data)} bytes")
            print()
            
            print("=== Starting bitmap transmission ===")
            
            # Step 1: Send start marker
            print("Sending start marker...")
            ser.write(b'BMPStart\\n')
            ser.flush()
            
            # Step 2: Send dimensions  
            print(f"Sending dimensions: {width}x{height}")
            size_cmd = f"SIZE:{width},{height}\\n"
            ser.write(size_cmd.encode())
            ser.flush()
            
            # Wait for Arduino READY response
            ready_received = False
            start_time = time.time()
            while time.time() - start_time < 5:
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        print(f"Arduino: {response}")
                        if response == "READY":
                            ready_received = True
                            break
                time.sleep(0.1)
            
            if not ready_received:
                print("Warning: READY response not received, continuing...")
            
            # Step 3: Send pixel data
            print(f"Sending {len(pixel_data)//2} pixels...")
            
            # Send pixel data in smaller chunks to prevent overload
            chunk_size = 500  # Conservative chunk size
            total_bytes = len(pixel_data)
            
            for i in range(0, total_bytes, chunk_size):
                chunk = pixel_data[i:i+chunk_size]
                ser.write(bytes(chunk))
                
                # Show progress every 1000 pixels (2000 bytes)
                pixels_sent = (i + len(chunk)) // 2
                total_pixels = total_bytes // 2
                if pixels_sent % 1000 == 0 or i + len(chunk) >= total_bytes:
                    progress = (i + len(chunk)) / total_bytes * 100
                    print(f"Progress: {progress:.1f}% ({pixels_sent}/{total_pixels} pixels, {i + len(chunk)} bytes)")
                
                # Small delay to prevent Arduino overload
                time.sleep(0.005)  # 5ms delay between chunks
            
            print(f"Pixel data sent: {total_bytes} bytes")
            
            # Step 4: Send end marker
            print("Sending end marker...")
            ser.write(b'BMPEnd\\n')
            ser.flush()
            
            # Read Arduino responses during and after transmission
            print("Waiting for completion confirmation...")
            start_time = time.time()
            while time.time() - start_time < 10:
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        print(f"Arduino: {response}")
                        if "COMPLETE" in response:
                            break
                time.sleep(0.1)
            
            print("✓ Bitmap transmission completed successfully!")
            
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
        print("Check that:")
        print("1. Arduino Due is connected via programming port")
        print("2. No other programs are using the serial port")
        print("3. Port is correct (usually /dev/ttyACM0)")
    except KeyboardInterrupt:
        print("\\nTransmission interrupted by user")
    except Exception as e:
        print(f"Error during transmission: {e}")

def main():
    if len(sys.argv) != 2:
        print("ST7735 Dual Display - Bitmap Sender")
        print("Usage: python3 bitmap_sender.py <image_path>")
        print("Example: python3 bitmap_sender.py ./tiger.png")
        print()
        print("This version is compatible with the dual display Arduino firmware.")
        print("It will send images to Display 1 without interfering with Display 2 (clock).")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        sys.exit(1)
    
    print(f"Processing image for Display 1: {image_path}")
    
    # Process the image for Display 1 specifications
    pixel_data, width, height = process_image_for_display1(image_path)
    if pixel_data is None:
        print("Failed to process image")
        sys.exit(1)
    
    print()
    
    # Send to Arduino using dual display protocol
    send_to_arduino_dual_display(pixel_data, width, height)
    
    print()
    print("✓ Operation completed successfully!")
    print("Disconnected from Arduino")

if __name__ == "__main__":
    main()