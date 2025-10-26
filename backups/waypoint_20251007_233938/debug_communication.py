#!/usr/bin/env python3
"""
Debug communication script to test Arduino serial protocol step by step
"""
import serial
import time

def debug_arduino_communication():
    try:
        # Connect to Arduino
        print("Connecting to Arduino Due on /dev/ttyACM0...")
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
        time.sleep(2)  # Wait for Arduino to initialize
        
        # Clear any buffered data
        ser.flushInput()
        ser.flushOutput()
        
        # Read initial messages
        print("\n=== Initial Arduino messages ===")
        for i in range(5):
            if ser.in_waiting > 0:
                msg = ser.readline().decode('utf-8').strip()
                print(f"Arduino: {msg}")
            time.sleep(0.1)
        
        # Test 1: Send BMPStart
        print("\n=== Test 1: Sending BMPStart ===")
        ser.write(b"BMPStart\n")
        ser.flush()
        time.sleep(0.5)
        
        # Read response
        for i in range(3):
            if ser.in_waiting > 0:
                msg = ser.readline().decode('utf-8').strip()
                print(f"Arduino response: {msg}")
            time.sleep(0.1)
        
        # Test 2: Send SIZE command
        print("\n=== Test 2: Sending SIZE:157,105 ===")
        ser.write(b"SIZE:157,105\n")
        ser.flush()
        time.sleep(0.5)
        
        # Read response
        for i in range(5):
            if ser.in_waiting > 0:
                msg = ser.readline().decode('utf-8').strip()
                print(f"Arduino response: {msg}")
            time.sleep(0.1)
        
        # Test 3: Send combined command (as in actual script)
        print("\n=== Test 3: Sending combined BMPStart\\nSIZE:157,105 ===")
        ser.write(b"BMPStart\nSIZE:157,105\n")
        ser.flush()
        time.sleep(0.5)
        
        # Read response
        for i in range(5):
            if ser.in_waiting > 0:
                msg = ser.readline().decode('utf-8').strip()
                print(f"Arduino response: {msg}")
            time.sleep(0.1)
        
        # Test 4: Check what's in buffer
        print(f"\n=== Buffer status ===")
        print(f"Bytes waiting: {ser.in_waiting}")
        if ser.in_waiting > 0:
            remaining = ser.read(ser.in_waiting)
            print(f"Remaining data: {remaining}")
        
        ser.close()
        print("\nDebug session complete")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_arduino_communication()