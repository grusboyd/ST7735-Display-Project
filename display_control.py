#!/usr/bin/env python3
"""
ST7735 Display Control Program - Unified GUI
Single program for all display control and image upload functions

Features:
- List displays
- Show display info
- Test displays
- Frame control
- Image upload with file picker
- Single serial connection to Native USB port (/dev/ttyACM0)

Requirements:
- Python 3.6+
- pyserial: pip install pyserial
- Pillow: pip install Pillow
- tkinter: (usually pre-installed with Python)

Usage:
    python3 display_control.py
"""

import sys
import time
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import serial
from PIL import Image, ImageOps
import struct
import json
import threading
import os
import fcntl
import toml

# Constants
SERIAL_BAUDRATE = 2000000  # 2 Mbps (Native USB ignores this, but set high for best performance)
TIMEOUT_SECONDS = 10
CHUNK_SIZE = 1024  # Send 1024 pixels (2048 bytes) at a time for faster transfers
SETTINGS_FILE = Path.home() / '.st7735_display_control.json'
DEFAULT_IMAGE_DIR = Path.home() / 'Pictures'
LOCK_FILE = '/tmp/st7735_display_control.lock'

def find_arduino_due_port():
    """Automatically detect Arduino Due Native USB port"""
    import glob
    import subprocess
    
    # Get all ttyACM ports
    ports = glob.glob('/dev/ttyACM*')
    
    if not ports:
        return None
    
    # Try to identify the Arduino Due by checking USB info
    for port in ports:
        try:
            # Get USB device info
            port_num = port.replace('/dev/ttyACM', '')
            result = subprocess.run(
                ['udevadm', 'info', '--name=' + port, '--attribute-walk'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Arduino Due Native USB shows up with specific identifiers
            if 'idVendor' in result.stdout:
                if '2341' in result.stdout or 'Arduino' in result.stdout:
                    # Check if it's the Native port (not Programming port)
                    # Native port typically has full permissions
                    stat = os.stat(port)
                    mode = oct(stat.st_mode)[-3:]
                    if mode == '666' or mode == '660':  # Read/write for user/group
                        return port
        except Exception as e:
            continue
    
    # Fallback: return the most recently modified port with proper permissions
    valid_ports = []
    for port in ports:
        try:
            stat = os.stat(port)
            mode = oct(stat.st_mode)[-3:]
            if mode in ['666', '660']:
                valid_ports.append((port, stat.st_mtime))
        except:
            continue
    
    if valid_ports:
        # Return the most recently modified port
        valid_ports.sort(key=lambda x: x[1], reverse=True)
        return valid_ports[0][0]
    
    # Last resort: return first available port
    return ports[0] if ports else None

class DisplayController:
    """Handles serial communication with unified CMD:/DISPLAY: protocol"""
    
    def __init__(self, serial_port=None, baudrate=SERIAL_BAUDRATE):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.connection = None
        self.active_display = None
        self.displays = []
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 2
        
    def connect(self, auto_reconnect=False):
        """Establish serial connection"""
        try:
            # Auto-detect port if not specified or if reconnecting
            if not self.serial_port or auto_reconnect:
                detected_port = find_arduino_due_port()
                if not detected_port:
                    print("ERROR: No Arduino Due port found!")
                    return False
                self.serial_port = detected_port
            
            print(f"Connecting to Arduino Due on {self.serial_port}...")
            self.connection = serial.Serial(
                self.serial_port,
                self.baudrate,
                timeout=TIMEOUT_SECONDS,
                write_timeout=TIMEOUT_SECONDS
            )
            
            # Wait for Arduino to initialize
            print("Waiting for Arduino to initialize...")
            time.sleep(3)
            
            # Read startup messages
            while self.connection.in_waiting > 0:
                line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Arduino: {line}")
            
            self.connection.reset_input_buffer()
            print("Connection established!")
            self.reconnect_attempts = 0  # Reset counter on success
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Disconnected from Arduino")
    
    def handle_connection_error(self, error_context=""):
        """Handle connection errors with intelligent reconnection"""
        print(f"Connection error in {error_context}: {type(self).__name__}")
        
        # Don't auto-reconnect if we've tried too many times
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return False
        
        self.reconnect_attempts += 1
        print(f"Attempting to reconnect (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        # Close existing connection
        try:
            if self.connection:
                self.connection.close()
        except:
            pass
        
        self.connection = None
        time.sleep(1)  # Brief delay before reconnecting
        
        # Try to reconnect with port detection
        return self.connect(auto_reconnect=True)
    
    def send_command(self, command):
        """Send a CMD: prefixed command and return response"""
        if not self.connection or not self.connection.is_open:
            return "ERROR:Not connected"
        
        try:
            # Send command with newline
            cmd = f"CMD:{command}\n"
            self.connection.write(cmd.encode('utf-8'))
            self.connection.flush()
            
            # Read response
            response_lines = []
            start_time = time.time()
            
            while time.time() - start_time < 5:  # 5 second timeout
                if self.connection.in_waiting > 0:
                    line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        # Check for end markers
                        if line.startswith('OK:') or line.startswith('ERROR:'):
                            if command in ['LIST', 'INFO', 'HELP']:
                                # Multi-line responses - wait for END marker
                                continue
                            else:
                                # Single-line response
                                break
                        if line.startswith('END_'):
                            break
                time.sleep(0.01)
            
            return '\n'.join(response_lines)
            
        except serial.SerialException as e:
            # Connection lost - try to reconnect unless it's a calibration command
            if command != 'CALIBRATE':
                if self.handle_connection_error(f"send_command({command})"):
                    # Reconnected - retry the command once
                    return self.send_command(command)
            return f"ERROR:Connection lost - {e}"
        except Exception as e:
            return f"ERROR:Communication failed - {e}"
    
    def get_display_list(self):
        """Get list of displays using CMD:LIST"""
        response = self.send_command('LIST')
        
        displays = []
        lines = response.split('\n')
        
        for line in lines:
            # Parse display entries from the response
            # Expected format: "[0] DueLCD01 - 160x128 (Unknown)"
            if line.strip().startswith('[') and ']' in line:
                # Extract display name between ']' and '-'
                parts = line.split(']', 1)
                if len(parts) > 1:
                    name_part = parts[1].split('-', 1)[0].strip()
                    if name_part:
                        displays.append(name_part)
        
        self.displays = displays
        return displays
    
    def select_display(self, display_name):
        """Select a display using DISPLAY: command"""
        if not self.connection or not self.connection.is_open:
            return "ERROR:Not connected"
        
        try:
            cmd = f"DISPLAY:{display_name}\n"
            self.connection.write(cmd.encode('utf-8'))
            self.connection.flush()
            
            # Wait for DISPLAY_READY response
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.connection.in_waiting > 0:
                    line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith('DISPLAY_READY'):
                        self.active_display = display_name
                        return f"OK:Display selected: {display_name}"
                    elif line.startswith('DISPLAY_ERROR') or line.startswith('ERROR'):
                        return f"ERROR:{line}"
                time.sleep(0.01)
            
            return "ERROR:Timeout waiting for display selection response"
            
        except Exception as e:
            return f"ERROR:Selection failed - {e}"
    
    def send_bitmap(self, image_path, progress_callback=None):
        """Send bitmap image using DISPLAY: protocol"""
        if not self.active_display:
            return "ERROR:No display selected. Use DISPLAY:<name> first."
        
        try:
            # Load and process image
            img = Image.open(image_path)
            
            # Get active display dimensions (assume 158x126 for now, could query via CMD:INFO)
            display_width = 158
            display_height = 126
            
            # Resize and fit image
            img = ImageOps.fit(img, (display_width, display_height), Image.Resampling.LANCZOS)
            img = img.convert('RGB')
            
            width, height = img.size
            
            if progress_callback:
                progress_callback(f"Sending bitmap: {width}x{height}")
            
            # Send BMPStart
            self.connection.write(b"BMPStart\n")
            self.connection.flush()
            response = self.connection.readline().decode('utf-8', errors='ignore').strip()
            if progress_callback:
                progress_callback(f"Arduino: {response}")
            
            # Send SIZE
            size_cmd = f"SIZE:{width},{height}\n"
            self.connection.write(size_cmd.encode('utf-8'))
            self.connection.flush()
            
            # Wait for READY
            while True:
                if self.connection.in_waiting > 0:
                    line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    if progress_callback:
                        progress_callback(f"Arduino: {line}")
                    if 'READY' in line:
                        break
                    if 'ERROR' in line:
                        return f"ERROR:{line}"
                time.sleep(0.01)
            
            # Send pixel data in batches for much faster transfer
            pixels = list(img.getdata())
            total_pixels = len(pixels)
            pixel_buffer = bytearray()
            
            for i, (r, g, b) in enumerate(pixels):
                # Convert RGB888 to RGB565
                r5 = (r >> 3) & 0x1F
                g6 = (g >> 2) & 0x3F
                b5 = (b >> 3) & 0x1F
                rgb565 = (r5 << 11) | (g6 << 5) | b5
                
                # Add pixel to buffer (big-endian uint16)
                pixel_buffer.extend(struct.pack('>H', rgb565))
                
                # Send batch when buffer is full
                if len(pixel_buffer) >= CHUNK_SIZE * 2:  # 2 bytes per pixel
                    self.connection.write(pixel_buffer)
                    pixel_buffer.clear()
                    
                    # Progress update
                    if progress_callback:
                        percent = (i / total_pixels) * 100
                        progress_callback(f"Sending pixels: {percent:.1f}%")
            
            # Send any remaining pixels
            if pixel_buffer:
                self.connection.write(pixel_buffer)
            
            self.connection.flush()
            
            if progress_callback:
                progress_callback("All pixels sent, waiting for Arduino...")
            
            # Send BMPEnd
            time.sleep(0.5)
            self.connection.write(b"BMPEnd\n")
            self.connection.flush()
            
            # Wait for COMPLETE
            while self.connection.in_waiting > 0:
                line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                if progress_callback:
                    progress_callback(f"Arduino: {line}")
                if 'COMPLETE' in line:
                    return "OK:Bitmap transfer complete"
            
            return "OK:Bitmap transfer complete"
            
        except serial.SerialException as e:
            # Connection lost during image transfer - don't auto-reconnect
            # User should manually reconnect and retry
            return f"ERROR:Connection lost during transfer - {e}"
        except Exception as e:
            return f"ERROR:Bitmap transfer failed - {e}"


class DisplayControlGUI:
    """Tkinter GUI for display control"""
    
    def __init__(self, master):
        self.master = master
        master.title("ST7735 Display Control v3.1")
        master.geometry("800x700")  # Increased size to prevent button clipping
        master.minsize(800, 700)  # Set minimum size
        
        self.controller = DisplayController()
        self.last_image_dir = self.load_settings().get('last_directory', str(DEFAULT_IMAGE_DIR))
        
        self.create_widgets()
        
        # Auto-connect on startup
        self.master.after(100, self.connect_to_arduino)
    
    def create_widgets(self):
        """Create GUI layout"""
        
        # Connection status
        status_frame = ttk.Frame(self.master, padding="10")
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Status: Disconnected", foreground="red")
        self.status_label.pack(side=tk.LEFT)
        
        self.activity_label = ttk.Label(status_frame, text="", foreground="blue", font=("TkDefaultFont", 9, "italic"))
        self.activity_label.pack(side=tk.LEFT, padx=20)
        
        self.reconnect_btn = ttk.Button(status_frame, text="Reconnect", command=self.connect_to_arduino)
        self.reconnect_btn.pack(side=tk.RIGHT)
        
        # Display selection
        display_frame = ttk.LabelFrame(self.master, text="Display Selection", padding="10")
        display_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # First row: List and Select
        select_row = ttk.Frame(display_frame)
        select_row.pack(fill=tk.X, pady=2)
        
        self.list_btn = ttk.Button(select_row, text="List Displays", command=self.list_displays, state='disabled')
        self.list_btn.pack(side=tk.LEFT, padx=5)
        
        self.display_var = tk.StringVar()
        self.display_combo = ttk.Combobox(select_row, textvariable=self.display_var, state='disabled', width=20)
        self.display_combo.pack(side=tk.LEFT, padx=5)
        
        self.select_btn = ttk.Button(select_row, text="Select Display", command=self.select_display, state='disabled')
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # Second row: Display info
        info_row = ttk.Frame(display_frame)
        info_row.pack(fill=tk.X, pady=2)
        
        self.display_info_label = ttk.Label(info_row, text="No display selected", foreground="gray")
        self.display_info_label.pack(side=tk.LEFT, padx=5)
        
        # Display operations
        ops_frame = ttk.LabelFrame(self.master, text="Display Operations", padding="10")
        ops_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_btn = ttk.Button(ops_frame, text="Show Info", command=self.show_info, state='disabled')
        self.info_btn.pack(side=tk.LEFT, padx=5)
        self.test_btn = ttk.Button(ops_frame, text="Test Display", command=self.test_display, state='disabled')
        self.test_btn.pack(side=tk.LEFT, padx=5)
        self.test_all_btn = ttk.Button(ops_frame, text="Test All", command=self.test_all_displays, state='disabled')
        self.test_all_btn.pack(side=tk.LEFT, padx=5)
        self.calibrate_btn = ttk.Button(ops_frame, text="Calibrate", command=self.calibrate_display, state='disabled')
        self.calibrate_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame controls
        frame_frame = ttk.LabelFrame(self.master, text="Frame Control", padding="10")
        frame_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.frame_on_btn = ttk.Button(frame_frame, text="Frame ON", command=lambda: self.frame_control('ON'), state='disabled')
        self.frame_on_btn.pack(side=tk.LEFT, padx=5)
        self.frame_off_btn = ttk.Button(frame_frame, text="Frame OFF", command=lambda: self.frame_control('OFF'), state='disabled')
        self.frame_off_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_frame, text="Color:").pack(side=tk.LEFT, padx=5)
        self.frame_color = ttk.Entry(frame_frame, width=10, state='disabled')
        self.frame_color.insert(0, "65535")  # White
        self.frame_color.pack(side=tk.LEFT, padx=5)
        self.frame_color_btn = ttk.Button(frame_frame, text="Set Color", command=self.set_frame_color, state='disabled')
        self.frame_color_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_frame, text="Thickness:").pack(side=tk.LEFT, padx=5)
        self.frame_thickness = ttk.Spinbox(frame_frame, from_=1, to=10, width=5, state='disabled')
        self.frame_thickness.set(1)
        self.frame_thickness.pack(side=tk.LEFT, padx=5)
        self.frame_thick_btn = ttk.Button(frame_frame, text="Set Thickness", command=self.set_frame_thickness, state='disabled')
        self.frame_thick_btn.pack(side=tk.LEFT, padx=5)
        
        # Image upload
        image_frame = ttk.LabelFrame(self.master, text="Image Upload", padding="10")
        image_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.upload_btn = ttk.Button(image_frame, text="Select and Upload Image", command=self.upload_image, width=30, state='disabled')
        self.upload_btn.pack(pady=5)
        
        # Console output
        console_frame = ttk.LabelFrame(self.master, text="Console", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.console = scrolledtext.ScrolledText(console_frame, height=15, wrap=tk.WORD)
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Create right-click context menu for console
        self.console_menu = tk.Menu(self.console, tearoff=0)
        self.console_menu.add_command(label="Copy", command=self.copy_selection, accelerator="Ctrl+C")
        self.console_menu.add_command(label="Select All", command=self.select_all_console, accelerator="Ctrl+A")
        self.console_menu.add_separator()
        self.console_menu.add_command(label="Copy All", command=self.copy_console)
        self.console_menu.add_command(label="Clear", command=lambda: self.console.delete(1.0, tk.END))
        
        # Bind right-click to show menu
        self.console.bind("<Button-3>", self.show_console_menu)
        
        # Bind keyboard shortcuts
        self.console.bind("<Control-c>", lambda e: self.copy_selection())
        self.console.bind("<Control-a>", lambda e: self.select_all_console())
        
        # Set initial button states
        self.update_button_states()
        
        # Help
        help_frame = ttk.Frame(self.master, padding="10")
        help_frame.pack(fill=tk.X)
        
        ttk.Button(help_frame, text="Show Protocol Help", command=self.show_help).pack(side=tk.LEFT, padx=5)
        ttk.Button(help_frame, text="Copy Console", command=self.copy_console).pack(side=tk.LEFT, padx=5)
        ttk.Button(help_frame, text="Clear Console", command=lambda: self.console.delete(1.0, tk.END)).pack(side=tk.RIGHT, padx=5)
    
    def log(self, message):
        """Log message to console"""
        self.console.insert(tk.END, f"{message}\n")
        self.console.see(tk.END)
        self.console.update()
    
    def connect_to_arduino(self):
        """Connect to Arduino"""
        self.log("Connecting to Arduino...")
        if self.controller.connect():
            port = self.controller.serial_port
            self.status_label.config(text=f"Status: Connected to {port}", foreground="green")
            self.log(f"Connected successfully on {port}!")
            self.update_button_states()
            # Auto-list displays
            self.master.after(500, self.list_displays)
        else:
            self.status_label.config(text="Status: Connection Failed", foreground="red")
            self.log("Connection failed. Check serial port.")
            self.update_button_states()
    
    def list_displays(self):
        """List available displays"""
        self.activity_label.config(text="Sending CMD:LIST...")
        self.master.update()
        self.log("Listing displays...")
        displays = self.controller.get_display_list()
        if displays:
            self.display_combo['values'] = displays
            if displays:
                self.display_combo.current(0)
            self.log(f"Found {len(displays)} display(s): {', '.join(displays)}")
        else:
            self.log("No displays found or communication error")
        self.update_button_states()
        self.activity_label.config(text="")
    
    def select_display(self):
        """Select active display"""
        display_name = self.display_var.get()
        if not display_name:
            self.log("ERROR: No display selected")
            return
        
        self.activity_label.config(text="Selecting display...")
        self.master.update()
        
        # Send RESET first to clear any previous state
        self.log("Resetting protocol state...")
        reset_response = self.controller.send_command('RESET')
        if reset_response:
            self.log(f"Reset: {reset_response}")
        
        # Wait for protocol to fully reset
        time.sleep(0.2)
        
        self.log(f"Selecting display: {display_name}")
        response = self.controller.select_display(display_name)
        self.log(response)
        self.update_button_states()
        self.activity_label.config(text="")
        
        # Automatically get and display info after selection
        if "OK" in response:
            self.master.after(100, self.show_info)
    
    def show_info(self):
        """Show display info"""
        self.activity_label.config(text="Sending CMD:INFO...")
        self.master.update()
        self.log("Getting display info...")
        response = self.controller.send_command('INFO')
        self.log(response)
        
        # Parse display info from response
        display_name = ""
        resolution = ""
        rotation = ""
        
        if response:
            for line in response.split('\n'):
                if line.startswith('Name:'):
                    display_name = line.split(':')[1].strip()
                elif line.startswith('Resolution:'):
                    resolution = line.split(':')[1].strip()
                elif line.startswith('Rotation:'):
                    rotation = line.split(':')[1].strip()
                elif line.startswith('FrameColor:'):
                    color = line.split(':')[1].strip()
                    self.frame_color.delete(0, tk.END)
                    self.frame_color.insert(0, color)
                elif line.startswith('FrameThickness:'):
                    thickness = line.split(':')[1].strip()
                    self.frame_thickness.delete(0, tk.END)
                    self.frame_thickness.insert(0, thickness)
            
            # Update display info label
            if display_name and resolution and rotation:
                info_text = f"{display_name} - {resolution} - Rotation: {rotation}°"
                self.display_info_label.config(text=info_text, foreground="black")
        
        self.activity_label.config(text="")
    
    def test_display(self):
        """Test active display"""
        self.activity_label.config(text="Sending CMD:TEST...")
        self.master.update()
        self.log("Testing active display...")
        response = self.controller.send_command('TEST')
        self.log(response)
        self.activity_label.config(text="")
    
    def calibrate_display(self):
        """Show calibration pattern in a dialog window"""
        if not self.controller.active_display:
            messagebox.showwarning("No Display", "Please select a display first")
            return
        
        # Create calibration dialog
        cal_dialog = tk.Toplevel(self.master)
        cal_dialog.title("Display Calibration")
        cal_dialog.geometry("600x650")
        cal_dialog.transient(self.master)
        cal_dialog.grab_set()
        
        # Store original frame values for cancel operation
        original_color = self.frame_color.get()
        original_thickness = self.frame_thickness.get()
        
        # Get display info to calculate bounds
        response = self.controller.send_command('INFO')
        center_x, center_y = 80, 65  # Default fallback
        usable_x, usable_y = 1, 1
        usable_width, usable_height = 158, 126
        display_width, display_height = 160, 128
        
        if "OK" in response:
            for line in response.split('\n'):
                if line.startswith('CenterX:'):
                    center_x = int(line.split(':')[1].strip())
                elif line.startswith('CenterY:'):
                    center_y = int(line.split(':')[1].strip())
                elif line.startswith('UsableX:'):
                    usable_x = int(line.split(':')[1].strip())
                elif line.startswith('UsableY:'):
                    usable_y = int(line.split(':')[1].strip())
                elif line.startswith('UsableWidth:'):
                    usable_width = int(line.split(':')[1].strip())
                elif line.startswith('UsableHeight:'):
                    usable_height = int(line.split(':')[1].strip())
                elif line.startswith('Width:'):
                    display_width = int(line.split(':')[1].strip())
                elif line.startswith('Height:'):
                    display_height = int(line.split(':')[1].strip())
        
        # Calculate bounds properly:
        # Inner bound: center ± 10 pixels (prevent sides from crossing center)
        # Outer bound: ±10 pixels from published display dimensions
        # 
        # For TOP: can move from (center_y + 10) to -10 (beyond top edge)
        # For BOTTOM: can move from (center_y - 10) to (display_height + 10 - (usable_y + usable_height))
        # For LEFT: can move from (center_x + 10) to -10 (beyond left edge)
        # FOR RIGHT: can move from (center_x - 10) to (display_width + 10 - (usable_x + usable_width))
        
        # Max adjustment = how far edge can move from its current position
        # Top edge is at usable_y, can go to max((center_y + 10), -10)
        max_top_adjust = usable_y + 10  # Can go 10 pixels beyond top edge
        max_bottom_adjust = (display_height - (usable_y + usable_height)) + 10
        max_left_adjust = usable_x + 10  # Can go 10 pixels beyond left edge
        max_right_adjust = (display_width - (usable_x + usable_width)) + 10
        
        # Get current adjustments from firmware BEFORE creating spinboxes
        current_adjust_top = 0
        current_adjust_bottom = 0
        current_adjust_left = 0
        current_adjust_right = 0
        
        if "OK" in response:
            for line in response.split('\n'):
                if line.startswith('UsableAreaAdjustTop:'):
                    current_adjust_top = int(line.split(':')[1].strip())
                elif line.startswith('UsableAreaAdjustBottom:'):
                    current_adjust_bottom = int(line.split(':')[1].strip())
                elif line.startswith('UsableAreaAdjustLeft:'):
                    current_adjust_left = int(line.split(':')[1].strip())
                elif line.startswith('UsableAreaAdjustRight:'):
                    current_adjust_right = int(line.split(':')[1].strip())
        
        # Store original offset values for cancel operation (after loading from firmware)
        original_offsets = {
            'TOP': current_adjust_top,
            'BOTTOM': current_adjust_bottom,
            'LEFT': current_adjust_left,
            'RIGHT': current_adjust_right
        }
        
        # Display info
        info_frame = ttk.LabelFrame(cal_dialog, text="Display Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Display: {self.controller.active_display}", 
                 font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Center: ({center_x}, {center_y})  |  Max adjustment: ±{min(max_top_adjust, max_left_adjust)} pixels",
                 font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        ttk.Label(info_frame, text="The calibration pattern shows a frame with corner markers", 
                 wraplength=550).pack(anchor=tk.W, pady=5)
        ttk.Label(info_frame, text="and a center crosshair to verify display alignment.", 
                 wraplength=550).pack(anchor=tk.W)
        
        # Frame parameters
        params_frame = ttk.LabelFrame(cal_dialog, text="Frame Parameters", padding="10")
        params_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Frame ON/OFF row
        frame_toggle_row = ttk.Frame(params_frame)
        frame_toggle_row.pack(fill=tk.X, pady=5)
        ttk.Label(frame_toggle_row, text="Frame:").pack(side=tk.LEFT, padx=5)
        
        def toggle_frame_on():
            status_label.config(text="Enabling frame...", foreground="blue")
            cal_dialog.update()
            response = self.controller.send_command('FRAME_ON')
            if "OK" in response:
                status_label.config(text="✓ Frame enabled", foreground="green")
                show_pattern()
            else:
                status_label.config(text=f"✗ Error: {response}", foreground="red")
        
        def toggle_frame_off():
            status_label.config(text="Disabling frame...", foreground="blue")
            cal_dialog.update()
            response = self.controller.send_command('FRAME_OFF')
            if "OK" in response:
                status_label.config(text="✓ Frame disabled", foreground="green")
            else:
                status_label.config(text=f"✗ Error: {response}", foreground="red")
        
        ttk.Button(frame_toggle_row, text="ON", command=toggle_frame_on, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_toggle_row, text="OFF", command=toggle_frame_off, width=8).pack(side=tk.LEFT, padx=5)
        
        # Color row
        color_row = ttk.Frame(params_frame)
        color_row.pack(fill=tk.X, pady=5)
        ttk.Label(color_row, text="Color (RGB565):").pack(side=tk.LEFT, padx=5)
        color_entry = ttk.Entry(color_row, width=10)
        color_entry.insert(0, self.frame_color.get())
        color_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(color_row, text="(0-65535, White=65535, Red=63488, Green=2016, Blue=31)").pack(side=tk.LEFT, padx=5)
        
        # Thickness row
        thick_row = ttk.Frame(params_frame)
        thick_row.pack(fill=tk.X, pady=5)
        ttk.Label(thick_row, text="Thickness:").pack(side=tk.LEFT, padx=5)
        thick_spin = ttk.Spinbox(thick_row, from_=1, to=10, width=8)
        thick_spin.set(self.frame_thickness.get())
        thick_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(thick_row, text="(1-10 pixels)").pack(side=tk.LEFT, padx=5)
        
        # Orientation row
        orient_row = ttk.Frame(params_frame)
        orient_row.pack(fill=tk.X, pady=5)
        ttk.Label(orient_row, text="Orientation:").pack(side=tk.LEFT, padx=5)
        
        def set_orientation(orient_value):
            status_label.config(text=f"Setting orientation to {orient_value}...", foreground="blue")
            cal_dialog.update()
            response = self.controller.send_command(f'ORIENTATION:{orient_value}')
            if "OK" in response:
                status_label.config(text=f"✓ Orientation set to {orient_value}", foreground="green")
            else:
                status_label.config(text=f"✗ Error: {response}", foreground="red")
        
        ttk.Button(orient_row, text="Portrait (0)", command=lambda: set_orientation(0), width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(orient_row, text="Landscape (1)", command=lambda: set_orientation(1), width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(orient_row, text="Rev Portrait (2)", command=lambda: set_orientation(2), width=14).pack(side=tk.LEFT, padx=2)
        ttk.Button(orient_row, text="Rev Landscape (3)", command=lambda: set_orientation(3), width=15).pack(side=tk.LEFT, padx=2)
        
        # Frame Position Offsets
        offset_frame = ttk.LabelFrame(cal_dialog, text="Frame Position Offsets (pixels)", padding="10")
        offset_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Hint label
        hint_label = ttk.Label(offset_frame, 
                              text="Click: Move edge  |  Shift+Click: Adjust width/height",
                              font=("TkDefaultFont", 8, "italic"),
                              foreground="gray")
        hint_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Individual side offsets
        offset_sides_frame = ttk.Frame(offset_frame)
        offset_sides_frame.pack(fill=tk.X, pady=5)
        
        # Top offset
        top_frame = ttk.Frame(offset_sides_frame)
        top_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(top_frame, text="Top:").pack(side=tk.LEFT)
        offset_top = ttk.Spinbox(top_frame, from_=-max_top_adjust, to=max_top_adjust, width=6, increment=1)
        offset_top.set(current_adjust_top)  # Load current value from firmware
        offset_top.pack(side=tk.LEFT, padx=2)
        offset_top.bind('<Return>', lambda e: apply_offset('TOP', int(offset_top.get())))
        
        def adjust_top(delta, shift=False):
            if shift:
                # Shift+click: adjust height
                # Top+: increase height (top UP=-1, bottom DOWN=+1)
                # Top-: decrease height (top DOWN=+1, bottom UP=-1)
                current_top = int(offset_top.get())
                current_bottom = int(offset_bottom.get())
                new_top = max(-max_top_adjust, min(max_top_adjust, current_top - delta))
                new_bottom = max(-max_bottom_adjust, min(max_bottom_adjust, current_bottom - delta))
                offset_top.set(new_top)
                offset_bottom.set(new_bottom)
                apply_offset('TOP', new_top)
                apply_offset('BOTTOM', new_bottom)
            else:
                # Normal click: move top edge only
                current = int(offset_top.get())
                new_val = max(-max_top_adjust, min(max_top_adjust, current + delta))
                offset_top.set(new_val)
                apply_offset('TOP', new_val)
        
        top_plus_btn = ttk.Button(top_frame, text="+", width=3)
        top_plus_btn.pack(side=tk.LEFT, padx=1)
        top_plus_btn.bind('<Button-1>', lambda e: adjust_top(1, e.state & 0x1))
        
        top_minus_btn = ttk.Button(top_frame, text="-", width=3)
        top_minus_btn.pack(side=tk.LEFT, padx=1)
        top_minus_btn.bind('<Button-1>', lambda e: adjust_top(-1, e.state & 0x1))
        
        # Bottom offset
        bottom_frame = ttk.Frame(offset_sides_frame)
        bottom_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(bottom_frame, text="Bottom:").pack(side=tk.LEFT)
        offset_bottom = ttk.Spinbox(bottom_frame, from_=-max_bottom_adjust, to=max_bottom_adjust, width=6, increment=1)
        offset_bottom.set(current_adjust_bottom)  # Load current value from firmware
        offset_bottom.pack(side=tk.LEFT, padx=2)
        offset_bottom.bind('<Return>', lambda e: apply_offset('BOTTOM', int(offset_bottom.get())))
        
        def adjust_bottom(delta, shift=False):
            if shift:
                # Shift+click: adjust height
                # Bottom+: increase height (bottom DOWN=+1, top UP=-1)
                # Bottom-: decrease height (bottom UP=-1, top DOWN=+1)
                current_top = int(offset_top.get())
                current_bottom = int(offset_bottom.get())
                new_top = max(-max_top_adjust, min(max_top_adjust, current_top - delta))
                new_bottom = max(-max_bottom_adjust, min(max_bottom_adjust, current_bottom - delta))
                offset_top.set(new_top)
                offset_bottom.set(new_bottom)
                apply_offset('TOP', new_top)
                apply_offset('BOTTOM', new_bottom)
            else:
                # Normal click: move bottom edge only
                current = int(offset_bottom.get())
                new_val = max(-max_bottom_adjust, min(max_bottom_adjust, current + delta))
                offset_bottom.set(new_val)
                apply_offset('BOTTOM', new_val)
        
        bottom_plus_btn = ttk.Button(bottom_frame, text="+", width=3)
        bottom_plus_btn.pack(side=tk.LEFT, padx=1)
        bottom_plus_btn.bind('<Button-1>', lambda e: adjust_bottom(1, e.state & 0x1))
        
        bottom_minus_btn = ttk.Button(bottom_frame, text="-", width=3)
        bottom_minus_btn.pack(side=tk.LEFT, padx=1)
        bottom_minus_btn.bind('<Button-1>', lambda e: adjust_bottom(-1, e.state & 0x1))
        
        # Left offset
        left_frame = ttk.Frame(offset_frame)
        left_frame.pack(fill=tk.X, pady=5)
        left_inner = ttk.Frame(left_frame)
        left_inner.pack(side=tk.LEFT, padx=10)
        ttk.Label(left_inner, text="Left:").pack(side=tk.LEFT)
        offset_left = ttk.Spinbox(left_inner, from_=-max_left_adjust, to=max_left_adjust, width=6, increment=1)
        offset_left.set(current_adjust_left)  # Load current value from firmware
        offset_left.pack(side=tk.LEFT, padx=2)
        offset_left.bind('<Return>', lambda e: apply_offset('LEFT', int(offset_left.get())))
        
        def adjust_left(delta, shift=False):
            if shift:
                # Shift+click: adjust width
                # Left+: increase width (left LEFT=-1, right RIGHT=+1)
                # Left-: decrease width (left RIGHT=+1, right LEFT=-1)
                current_left = int(offset_left.get())
                current_right = int(offset_right.get())
                new_left = max(-max_left_adjust, min(max_left_adjust, current_left - delta))
                new_right = max(-max_right_adjust, min(max_right_adjust, current_right - delta))
                offset_left.set(new_left)
                offset_right.set(new_right)
                apply_offset('LEFT', new_left)
                apply_offset('RIGHT', new_right)
            else:
                # Normal click: move left edge only
                current = int(offset_left.get())
                new_val = max(-max_left_adjust, min(max_left_adjust, current + delta))
                offset_left.set(new_val)
                apply_offset('LEFT', new_val)
        
        left_plus_btn = ttk.Button(left_inner, text="+", width=3)
        left_plus_btn.pack(side=tk.LEFT, padx=1)
        left_plus_btn.bind('<Button-1>', lambda e: adjust_left(1, e.state & 0x1))
        
        left_minus_btn = ttk.Button(left_inner, text="-", width=3)
        left_minus_btn.pack(side=tk.LEFT, padx=1)
        left_minus_btn.bind('<Button-1>', lambda e: adjust_left(-1, e.state & 0x1))
        
        # Right offset
        right_inner = ttk.Frame(left_frame)
        right_inner.pack(side=tk.LEFT, padx=10)
        ttk.Label(right_inner, text="Right:").pack(side=tk.LEFT)
        offset_right = ttk.Spinbox(right_inner, from_=-max_right_adjust, to=max_right_adjust, width=6, increment=1)
        offset_right.set(current_adjust_right)  # Load current value from firmware
        offset_right.pack(side=tk.LEFT, padx=2)
        offset_right.bind('<Return>', lambda e: apply_offset('RIGHT', int(offset_right.get())))
        
        def adjust_right(delta, shift=False):
            if shift:
                # Shift+click: adjust width
                # Right+: increase width (right RIGHT=+1, left LEFT=-1)
                # Right-: decrease width (right LEFT=-1, left RIGHT=+1)
                current_left = int(offset_left.get())
                current_right = int(offset_right.get())
                new_left = max(-max_left_adjust, min(max_left_adjust, current_left - delta))
                new_right = max(-max_right_adjust, min(max_right_adjust, current_right - delta))
                offset_left.set(new_left)
                offset_right.set(new_right)
                apply_offset('LEFT', new_left)
                apply_offset('RIGHT', new_right)
            else:
                # Normal click: move right edge only
                current = int(offset_right.get())
                new_val = max(-max_right_adjust, min(max_right_adjust, current + delta))
                offset_right.set(new_val)
                apply_offset('RIGHT', new_val)
        
        right_plus_btn = ttk.Button(right_inner, text="+", width=3)
        right_plus_btn.pack(side=tk.LEFT, padx=1)
        right_plus_btn.bind('<Button-1>', lambda e: adjust_right(1, e.state & 0x1))
        
        right_minus_btn = ttk.Button(right_inner, text="-", width=3)
        right_minus_btn.pack(side=tk.LEFT, padx=1)
        right_minus_btn.bind('<Button-1>', lambda e: adjust_right(-1, e.state & 0x1))
        
        # Move all sides together
        all_frame = ttk.Frame(offset_frame)
        all_frame.pack(fill=tk.X, pady=5)
        ttk.Label(all_frame, text="Move All Sides:").pack(side=tk.LEFT, padx=10)
        
        def move_all(direction):
            """Move all sides in the same direction (translation, not resize)"""
            if direction == 'up':
                adjust_top(-1, shift=False)
                adjust_bottom(-1, shift=False)
            elif direction == 'down':
                adjust_top(1, shift=False)
                adjust_bottom(1, shift=False)
            elif direction == 'left':
                # Move frame left: both edges move left
                # Note: LEFT adjustment is inverted in firmware (+ moves right, - moves left)
                adjust_left(-1, shift=False)   # Left edge moves left (negative because inverted)
                adjust_right(-1, shift=False)  # Right edge moves left (negative)
            elif direction == 'right':
                # Move frame right: both edges move right
                # Note: LEFT adjustment is inverted in firmware (+ moves right, - moves left)
                adjust_left(1, shift=False)   # Left edge moves right (positive because inverted)
                adjust_right(1, shift=False)  # Right edge moves right (positive)
        
        ttk.Button(all_frame, text="↑ Up", command=lambda: move_all('up'), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(all_frame, text="↓ Down", command=lambda: move_all('down'), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(all_frame, text="← Left", command=lambda: move_all('left'), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(all_frame, text="→ Right", command=lambda: move_all('right'), width=8).pack(side=tk.LEFT, padx=2)
        
        def apply_offset(side, value):
            """Apply offset to one side and refresh pattern"""
            response = self.controller.send_command(f'ADJUST_{side}:{value}')
            if "OK" in response:
                status_label.config(text=f"✓ Adjusted {side}: {value}", foreground="green")
            else:
                status_label.config(text=f"✗ Offset Error: {response}", foreground="red")
        
        # Control buttons
        control_frame = ttk.Frame(cal_dialog, padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def apply_params():
            """Apply frame parameters without closing dialog"""
            color = color_entry.get()
            thickness = thick_spin.get()
            
            status_label.config(text="Applying frame parameters...", foreground="blue")
            cal_dialog.update()
            
            # Set color
            response = self.controller.send_command(f'FRAME_COLOR:{color}')
            if "ERROR" in response:
                status_label.config(text=f"✗ Color Error: {response}", foreground="red")
                return
            
            # Set thickness
            response = self.controller.send_command(f'FRAME_THICKNESS:{thickness}')
            if "ERROR" in response:
                status_label.config(text=f"✗ Thickness Error: {response}", foreground="red")
                return
            
            status_label.config(text="✓ Parameters applied", foreground="green")
            show_pattern()
        
        def show_pattern():
            status_label.config(text="Sending calibration pattern...", foreground="blue")
            cal_dialog.update()
            response = self.controller.send_command('CALIBRATE')
            if "OK" in response:
                status_label.config(text="✓ Calibration pattern displayed", foreground="green")
            else:
                status_label.config(text=f"✗ Error: {response}", foreground="red")
        
        def clear_display():
            status_label.config(text="Clearing display...", foreground="blue")
            cal_dialog.update()
            response = self.controller.send_command('TEST')
            if "OK" in response:
                status_label.config(text="✓ Display cleared", foreground="green")
            else:
                status_label.config(text=f"✗ Error: {response}", foreground="red")
        
        def reset_offsets():
            """Reset all offsets to zero"""
            offset_top.set(0)
            offset_bottom.set(0)
            offset_left.set(0)
            offset_right.set(0)
            for side in ['TOP', 'BOTTOM', 'LEFT', 'RIGHT']:
                self.controller.send_command(f'ADJUST_{side}:0')
            status_label.config(text="✓ Offsets reset", foreground="green")
        
        def save_and_exit():
            """Save calibration to .config file and close"""
            # Get current display info
            response = self.controller.send_command('INFO')
            if "ERROR" in response or "OK" not in response:
                messagebox.showerror("Error", "Cannot get display info")
                return
            
            # Parse display name
            display_name = None
            lines = response.split('\n')
            for line in lines:
                if line.startswith('Name:'):
                    display_name = line.split(':')[1].strip()
            
            if not display_name:
                messagebox.showerror("Error", "Cannot determine display name")
                return
            
            # Find .config file
            config_file = Path(display_name + ".config")
            if not config_file.exists():
                messagebox.showerror("Error", f"Config file not found: {config_file}")
                return
            
            # Read current config file and extract current usable area
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Extract current usable area coordinates
                usable_x = None
                right = None
                usable_y = None
                bottom = None
                
                match = re.search(r'left\s*=\s*(\d+)', content)
                if match:
                    usable_x = int(match.group(1))
                match = re.search(r'right\s*=\s*(\d+)', content)
                if match:
                    right = int(match.group(1))
                match = re.search(r'top\s*=\s*(\d+)', content)
                if match:
                    usable_y = int(match.group(1))
                match = re.search(r'bottom\s*=\s*(\d+)', content)
                if match:
                    bottom = int(match.group(1))
                
                if None in [usable_x, right, usable_y, bottom]:
                    messagebox.showerror("Error", "Cannot parse config file - missing calibration values")
                    return
                
                # Calculate new calibration values from adjustments
                # Note: adjustments are inverted for top/left in firmware
                new_left = usable_x - int(offset_left.get())    # Inverted
                new_right = right + int(offset_right.get())
                new_top = usable_y - int(offset_top.get())      # Inverted
                new_bottom = bottom + int(offset_bottom.get())
                
                # Calculate new center
                new_center_x = new_left + (new_right - new_left + 1) // 2
                new_center_y = new_top + (new_bottom - new_top + 1) // 2
                
                # Update config file
                content = re.sub(r'left\s*=\s*\d+', f'left = {new_left}', content)
                content = re.sub(r'right\s*=\s*\d+', f'right = {new_right}', content)
                content = re.sub(r'top\s*=\s*\d+', f'top = {new_top}', content)
                content = re.sub(r'bottom\s*=\s*\d+', f'bottom = {new_bottom}', content)
                content = re.sub(r'center\s*=\s*\[\d+,\s*\d+\]', f'center = [{new_center_x}, {new_center_y}]', content)
                
                # Write back to file
                with open(config_file, 'w') as f:
                    f.write(content)
                
                # Push new calibration to firmware (reads from updated .config file values)
                update_cmd = f'UPDATE_CONFIG:{new_left},{new_right},{new_top},{new_bottom},{new_center_x},{new_center_y}'
                response = self.controller.send_command(update_cmd)
                
                if "OK" in response:
                    messagebox.showinfo("Calibration Saved", 
                        f"✓ Saved to {config_file}\n"
                        f"✓ Updated firmware configuration\n\n"
                        f"New usable area:\n"
                        f"  Left: {new_left}, Right: {new_right}\n"
                        f"  Top: {new_top}, Bottom: {new_bottom}\n"
                        f"New center: ({new_center_x}, {new_center_y})\n\n"
                        f"Changes are now active and permanent!")
                else:
                    messagebox.showwarning("Save Error",
                        f"✓ Saved to {config_file}\n"
                        f"✗ Failed to update firmware: {response}\n\n"
                        f"Reconnect or restart to apply changes.")
                
                # Save frame color/thickness to GUI
                self.frame_color.delete(0, tk.END)
                self.frame_color.insert(0, color_entry.get())
                self.frame_thickness.set(thick_spin.get())
                cal_dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save config: {e}")
        
        
        def cancel_and_exit():
            """Restore parameters from .config file and close"""
            # Read .config file to get stored calibration values
            config_file = f"{self.controller.active_display}.config"
            if Path(config_file).exists():
                try:
                    config = toml.load(config_file)
                    left = config['calibration']['left']
                    right = config['calibration']['right']
                    top = config['calibration']['top']
                    bottom = config['calibration']['bottom']
                    center_x, center_y = config['calibration']['center']
                    
                    # Send UPDATE_CONFIG to restore values from .config file
                    cmd = f"UPDATE_CONFIG:{left},{right},{top},{bottom},{center_x},{center_y}"
                    response = self.controller.send_command(cmd)
                    print(f"Restored config from file: {response}")
                except Exception as e:
                    print(f"Error reading .config file: {e}")
                    # Fallback: restore to original values from when dialog opened
                    self.controller.send_command(f'ADJUST_TOP:{original_offsets.get("TOP", 0)}')
                    self.controller.send_command(f'ADJUST_BOTTOM:{original_offsets.get("BOTTOM", 0)}')
                    self.controller.send_command(f'ADJUST_LEFT:{original_offsets.get("LEFT", 0)}')
                    self.controller.send_command(f'ADJUST_RIGHT:{original_offsets.get("RIGHT", 0)}')
            
            # Restore original color/thickness
            self.controller.send_command(f'FRAME_COLOR:{original_color}')
            self.controller.send_command(f'FRAME_THICKNESS:{original_thickness}')
            cal_dialog.destroy()
        
        ttk.Button(control_frame, text="Apply Color/Thickness", 
                  command=apply_params, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset Offsets", 
                  command=reset_offsets, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Display", 
                  command=clear_display, width=15).pack(side=tk.LEFT, padx=5)
        
        # Status label
        status_label = ttk.Label(cal_dialog, text="", foreground="blue")
        status_label.pack(pady=10)
        
        # Action buttons frame (bottom)
        action_frame = ttk.Frame(cal_dialog, padding="10")
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(action_frame, text="Save & Exit", 
                  command=save_and_exit, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Cancel", 
                  command=cancel_and_exit, width=15).pack(side=tk.RIGHT, padx=5)
        
        # Bind ESC key to cancel
        cal_dialog.bind('<Escape>', lambda e: cancel_and_exit())
        
        # Clear display then show pattern automatically on open
        def init_calibration():
            clear_display()
            cal_dialog.after(200, show_pattern)
        
        cal_dialog.after(100, init_calibration)
    
    def test_all_displays(self):
        """Test all displays"""
        self.activity_label.config(text="Sending CMD:TEST_ALL...")
        self.master.update()
        self.log("Testing all displays...")
        response = self.controller.send_command('TEST_ALL')
        self.log(response)
        self.activity_label.config(text="")
    
    def frame_control(self, state):
        """Enable/disable frame"""
        self.activity_label.config(text=f"Sending CMD:FRAME_{state}...")
        self.master.update()
        self.log(f"Setting frame {state}...")
        response = self.controller.send_command(f'FRAME_{state}')
        self.log(response)
        self.activity_label.config(text="")
    
    def set_frame_color(self):
        """Set frame color"""
        color = self.frame_color.get()
        self.activity_label.config(text=f"Setting frame color...")
        self.master.update()
        self.log(f"Setting frame color to {color}...")
        response = self.controller.send_command(f'FRAME_COLOR:{color}')
        self.log(response)
        self.activity_label.config(text="")
    
    def set_frame_thickness(self):
        """Set frame thickness"""
        thickness = self.frame_thickness.get()
        self.activity_label.config(text=f"Setting frame thickness...")
        self.master.update()
        self.log(f"Setting frame thickness to {thickness}...")
        response = self.controller.send_command(f'FRAME_THICKNESS:{thickness}')
        self.log(response)
        self.activity_label.config(text="")
    
    def show_help(self):
        """Show protocol help"""
        self.log("Getting protocol help...")
        response = self.controller.send_command('HELP')
        self.log(response)
    
    def copy_console(self):
        """Copy console contents to clipboard"""
        try:
            console_text = self.console.get(1.0, tk.END)
            self.master.clipboard_clear()
            self.master.clipboard_append(console_text)
            self.log("Console contents copied to clipboard!")
        except Exception as e:
            self.log(f"ERROR: Could not copy - {e}")
    
    def copy_selection(self):
        """Copy selected text to clipboard"""
        try:
            if self.console.tag_ranges(tk.SEL):
                selected_text = self.console.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.master.clipboard_clear()
                self.master.clipboard_append(selected_text)
        except Exception as e:
            pass  # No selection or error
    
    def select_all_console(self):
        """Select all text in console"""
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)
        return 'break'  # Prevent default behavior
    
    def show_console_menu(self, event):
        """Show context menu on right-click"""
        try:
            self.console_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.console_menu.grab_release()
    
    def update_button_states(self):
        """Update button states based on connection and display selection"""
        connected = self.controller.connection and self.controller.connection.is_open
        has_displays = len(self.controller.displays) > 0
        display_selected = self.controller.active_display is not None
        
        # Connection-dependent buttons
        state_connected = 'normal' if connected else 'disabled'
        self.list_btn['state'] = state_connected
        self.test_all_btn['state'] = state_connected
        
        # Display list dependent
        state_has_displays = 'readonly' if has_displays else 'disabled'
        self.display_combo['state'] = state_has_displays
        state_can_select = 'normal' if (connected and has_displays) else 'disabled'
        self.select_btn['state'] = state_can_select
        
        # Display selection dependent
        state_display = 'normal' if display_selected else 'disabled'
        self.info_btn['state'] = state_display
        self.test_btn['state'] = state_display
        self.calibrate_btn['state'] = state_display
        self.frame_on_btn['state'] = state_display
        self.frame_off_btn['state'] = state_display
        self.frame_color['state'] = state_display
        self.frame_color_btn['state'] = state_display
        self.frame_thickness['state'] = state_display
        self.frame_thick_btn['state'] = state_display
        self.upload_btn['state'] = state_display
    
    def upload_image(self):
        """Upload image to display"""
        if not self.controller.active_display:
            messagebox.showwarning("No Display", "Please select a display first")
            return
        
        # Open file picker
        filepath = filedialog.askopenfilename(
            title="Select Image",
            initialdir=self.last_image_dir,
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            # Save directory for next time
            self.last_image_dir = str(Path(filepath).parent)
            self.save_settings({'last_directory': self.last_image_dir})
            
            # Upload in separate thread to keep GUI responsive
            self.log(f"Uploading image: {filepath}")
            self.activity_label.config(text="Uploading image...")
            
            def upload_thread():
                response = self.controller.send_bitmap(filepath, progress_callback=self.log)
                self.log(f"Upload complete: {response}")
                self.master.after(0, lambda: self.activity_label.config(text=""))
            
            threading.Thread(target=upload_thread, daemon=True).start()
    
    def load_settings(self):
        """Load GUI settings"""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Could not load settings: {e}")
        return {}
    
    def save_settings(self, settings):
        """Save GUI settings"""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Could not save settings: {e}")
    
    def on_closing(self):
        """Handle window close"""
        self.controller.disconnect()
        self.master.destroy()


def main():
    """Main entry point"""
    # Check for single instance
    lock_file = None
    try:
        lock_file = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        # Another instance is running
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Already Running",
            "ST7735 Display Control is already running.\n\n"
            "Only one instance can be open at a time to prevent\n"
            "serial port conflicts."
        )
        root.destroy()
        sys.exit(1)
    
    try:
        root = tk.Tk()
        app = DisplayControlGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    finally:
        # Release the lock
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                os.unlink(LOCK_FILE)
            except:
                pass


if __name__ == "__main__":
    main()
