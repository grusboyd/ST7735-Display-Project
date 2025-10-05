#!/bin/bash

# ST7735 Display Project Repository Setup Script
# Author: grusboyd
# Date: October 5, 2025

set -e  # Exit on any error

echo "=========================================="
echo "ST7735 Display Project Repository Setup"
echo "=========================================="

# Configuration
PROJECT_NAME="ST7735_Display_Project"
GIT_USERNAME="grusboyd"
GIT_EMAIL="crank.drive@protonmail.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check if required tools are installed
print_step "Checking required tools..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    else
        print_success "$1 is available"
    fi
}

check_command git
check_command python3
check_command pip3

# Step 2: Get project location
read -p "Enter the full path where you want to create the project (default: /home/boyd/Documents/PlatformIO/Projects): " PROJECT_BASE
PROJECT_BASE=${PROJECT_BASE:-"/home/boyd/Documents/PlatformIO/Projects"}

if [ ! -d "$PROJECT_BASE" ]; then
    print_error "Directory $PROJECT_BASE does not exist!"
    exit 1
fi

PROJECT_PATH="$PROJECT_BASE/$PROJECT_NAME"

# Step 3: Create project directory
print_step "Creating project directory at $PROJECT_PATH..."
if [ -d "$PROJECT_PATH" ]; then
    print_warning "Directory already exists. Do you want to continue? (y/N)"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    mkdir -p "$PROJECT_PATH"
fi

cd "$PROJECT_PATH"

# Step 4: Initialize Git repository
print_step "Initializing Git repository..."
git init

# Step 5: Configure Git settings
print_step "Configuring Git settings..."
git config user.name "$GIT_USERNAME"
git config user.email "$GIT_EMAIL"
git config init.defaultBranch main

print_success "Git configured for user: $GIT_USERNAME <$GIT_EMAIL>"

# Step 6: Create project structure
print_step "Creating project structure..."

# Arduino project structure (PlatformIO)
mkdir -p arduino_code/{src,include,lib,test,tools}

# Raspberry Pi code structure
mkdir -p raspberry_pi_code

# Test images directory
mkdir -p test_images

# Documentation directory
mkdir -p docs/notebooks

print_success "Project directories created"

# Step 7: Create platformio.ini
print_step "Creating PlatformIO configuration..."
cat > arduino_code/platformio.ini << 'EOF'
[env:due]
platform = atmelsam
board = due
framework = arduino
lib_deps = 
    adafruit/Adafruit ST7735 and ST7789 Library@^1.10.3
    adafruit/Adafruit GFX Library@^1.11.9
    adafruit/Adafruit BusIO@^1.16.1
monitor_speed = 115200
EOF

# Step 8: Create virtual environment and install Python dependencies
print_step "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_step "Installing Python dependencies..."
pip install pillow pyserial numpy jupyter notebook

# Create requirements.txt
pip freeze > raspberry_pi_code/requirements.txt

print_success "Python environment set up"

# Step 9: Create README.md
print_step "Creating README.md..."
cat > README.md << 'EOF'
# ST7735 Display Project

A bitmap display system using an ST7735 LCD display connected to an Arduino Due, with image processing and transmission handled by a Raspberry Pi.

## Features

- 158x126 usable display area (from 160x128 total)
- RGB565 color format
- Automatic image scaling and centering
- Real-time serial communication
- Interactive calibration system
- Comprehensive error handling and validation

## Hardware Requirements

- ST7735 1.8" TFT LCD Display (160x128 pixels)
- Arduino Due
- Raspberry Pi (for image processing)
- USB cable for serial communication

## Pin Configuration

- CS = 7
- DC = 10
- RST = 8
- BL = 9

## Quick Start

1. Upload the Arduino code using PlatformIO
2. Activate Python virtual environment: `source venv/bin/activate`
3. Run image sender: `python raspberry_pi_code/bitmap_sender.py /path/to/image.png`

## Project Structure

- `arduino_code/` - PlatformIO project for Arduino Due
- `raspberry_pi_code/` - Python scripts for image processing
- `test_images/` - Sample images for testing
- `docs/notebooks/` - Jupyter notebooks with documentation

## Installation

See `docs/notebooks/` for detailed setup instructions.

EOF

# Step 10: Create comprehensive .gitignore
print_step "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
venv/
.env
.venv
pip-log.txt
pip-delete-this-directory.txt
.coverage
.pytest_cache/

# PlatformIO
.pio/
.vscode/.browse.c_cpp.db*
.vscode/c_cpp_properties.json
.vscode/launch.json
.vscode/ipch

# Arduino
*.hex
*.elf
*.map

# OS
.DS_Store
Thumbs.db
*~
.#*

# IDE
.vscode/settings.json
.idea/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Temporary files
*.tmp
*.bak
*.swp
*.swo

# Build artifacts
build/
dist/
*.egg-info/
EOF

# Step 11: Create placeholder files
print_step "Creating placeholder files..."

# Arduino main.cpp placeholder
cat > arduino_code/src/main.cpp << 'EOF'
// ST7735 Display Project - Main Arduino Code
// Hardware: Arduino Due with ST7735 LCD Display

#include <Arduino.h>
// TODO: Add your display code here

void setup() {
    Serial.begin(115200);
    // TODO: Initialize display
}

void loop() {
    // TODO: Main program loop
}
EOF

# Python bitmap sender placeholder
cat > raspberry_pi_code/bitmap_sender.py << 'EOF'
#!/usr/bin/env python3
"""
ST7735 Display Project - Bitmap Sender
Processes and transmits images to Arduino via serial connection
"""

import sys
from PIL import Image
import serial

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 bitmap_sender.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"Processing image: {image_path}")
    # TODO: Add image processing and transmission code

if __name__ == "__main__":
    main()
EOF

chmod +x raspberry_pi_code/bitmap_sender.py

# Step 12: Create initial Jupyter notebook
print_step "Creating documentation notebook..."
cat > docs/notebooks/Project_Documentation.ipynb << 'EOF'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# ST7735 Display Project Documentation\n",
    "\n",
    "This notebook contains comprehensive documentation for the ST7735 display project.\n",
    "\n",
    "## Project Overview\n",
    "\n",
    "- **Hardware**: ST7735 LCD with Arduino Due\n",
    "- **Software**: PlatformIO + Python image processing\n",
    "- **Communication**: Serial over USB\n",
    "- **Display Area**: 158x126 usable pixels"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
EOF

# Step 13: Add files to Git
print_step "Adding files to Git repository..."
git add .

# Step 14: Create initial commit
print_step "Creating initial commit..."
git commit -m "Initial commit: ST7735 Display Project setup

- Created project structure for Arduino Due and Raspberry Pi
- Added PlatformIO configuration for Arduino development  
- Set up Python environment with required dependencies
- Configured .gitignore for Python, Arduino, and IDE files
- Added project documentation and notebook templates
- Configured for user: $GIT_USERNAME <$GIT_EMAIL>"

# Step 15: Optional GitHub setup
print_step "Repository setup complete!"
echo
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo
echo "1. To connect to GitHub:"
echo "   - Create a new repository at: https://github.com/new"
echo "   - Repository name suggestion: 'ST7735-Display-Project'"
echo "   - Then run:"
echo "     cd $PROJECT_PATH"
echo "     git remote add origin https://github.com/$GIT_USERNAME/ST7735-Display-Project.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo
echo "2. To copy your existing code:"
echo "   - Copy Arduino code to: arduino_code/src/"
echo "   - Copy Python scripts to: raspberry_pi_code/"
echo "   - Copy test images to: test_images/"
echo
echo "3. To start development:"
echo "   cd $PROJECT_PATH"
echo "   source venv/bin/activate"
echo
print_success "Project created successfully at: $PROJECT_PATH"
echo

# Deactivate virtual environment
deactivate

print_success "Setup script completed!"