#!/bin/bash

# ST7735 Display Project - Direct Repository Publisher (from existing project)
# Author: grusboyd
# Date: October 5, 2025

set -e  # Exit on any error

echo "=========================================="
echo "ST7735 Project - Direct GitHub Publisher"
echo "=========================================="

# Configuration
GIT_USERNAME="grusboyd"
GIT_EMAIL="crank.drive@protonmail.com"
DEFAULT_REPO_NAME="ST7735-Display-Project"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "platformio.ini" ] || [ ! -d "src" ]; then
    print_error "This script must be run from your ST7735 PlatformIO project directory"
    print_info "Current directory: $(pwd)"
    print_info "Expected files: platformio.ini, src/ directory"
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)
print_info "Working in: $CURRENT_DIR"

# Check if this is already a git repository
if [ -d ".git" ]; then
    print_info "This directory is already a git repository"
    print_step "Checking git configuration..."
else
    print_step "Initializing git repository..."
    git init
fi

# Configure git if needed
git config user.name "$GIT_USERNAME" 2>/dev/null || true
git config user.email "$GIT_EMAIL" 2>/dev/null || true

# Create .gitignore if it doesn't exist or is minimal
if [ ! -f ".gitignore" ] || [ $(wc -l < .gitignore) -lt 10 ]; then
    print_step "Creating comprehensive .gitignore..."
    cat > .gitignore << 'EOF'
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

# Python (for companion scripts)
__pycache__/
*.py[cod]
*$py.class
*.so
venv/
.env
.venv

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
fi

# Create README.md if it doesn't exist
if [ ! -f "README.md" ]; then
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

- **ST7735 1.8" TFT LCD Display** (160x128 pixels)
- **Arduino Due**
- **Raspberry Pi** (for image processing)
- **USB cable** for serial communication

## Pin Configuration

- CS = 7 (Chip Select)
- DC = 10 (Data/Command)
- RST = 8 (Reset)
- BL = 9 (Backlight)

## Project Structure

```
ST7735onDue/
├── src/
│   └── main.cpp              # Main Arduino display code
├── tools/
│   └── cal_lcd.cpp           # Interactive calibration tool
├── platformio.ini            # PlatformIO configuration
└── README.md                 # This file
```

## Quick Start

1. **Upload Arduino Code**:
   ```bash
   platformio run --target upload
   ```

2. **Run Image Sender** (on Raspberry Pi):
   ```bash
   python3 bitmap_sender.py /path/to/image.png
   ```

## Display Specifications

- **Total Resolution**: 160x128 pixels
- **Usable Area**: 158x126 pixels (origin at 1,2)
- **Color Format**: RGB565
- **Orientation**: Landscape (automatic rotation handled)

## Calibration

The project includes an interactive calibration tool (`tools/cal_lcd.cpp`) for precise display boundary determination. Key calibrated values:

- Usable display area: 158x126 pixels
- Display origin offset: (1,2)
- Frame boundaries validated through interactive testing

## Development

Built with:
- **PlatformIO** for Arduino development
- **Adafruit ST7735 Library** for display control
- **Python PIL** for image processing
- **Serial communication** for data transmission

## Author

- **grusboyd** <crank.drive@protonmail.com>

## License

MIT License - See LICENSE file for details.
EOF
fi

# Get repository name
read -p "Enter GitHub repository name (default: $DEFAULT_REPO_NAME): " REPO_NAME
REPO_NAME=${REPO_NAME:-$DEFAULT_REPO_NAME}

# Get repository description
read -p "Enter repository description (optional): " REPO_DESCRIPTION
REPO_DESCRIPTION=${REPO_DESCRIPTION:-"ST7735 LCD Display Project with Arduino Due - Bitmap image transmission and display system with interactive calibration"}

# Ask about repository visibility
echo
print_info "Repository visibility options:"
echo "1. Public (recommended for open source)"
echo "2. Private"
read -p "Choose repository type (1 or 2, default: 1): " REPO_TYPE
REPO_TYPE=${REPO_TYPE:-1}

if [ "$REPO_TYPE" = "2" ]; then
    VISIBILITY_FLAG="--private"
else
    VISIBILITY_FLAG="--public"
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed."
    print_info "Install it with: curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    print_info "Then: echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list"
    print_info "Finally: sudo apt update && sudo apt install gh"
    exit 1
fi

# Check GitHub CLI authentication
print_step "Checking GitHub authentication..."
if ! gh auth status &> /dev/null; then
    print_info "You need to authenticate with GitHub."
    print_info "This will open a web browser for authentication."
    read -p "Press Enter to continue..."
    gh auth login
fi

print_success "GitHub authentication verified"

# Add all files to git
print_step "Adding project files to git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    print_info "No new changes to commit"
else
    # Create commit with detailed message
    COMMIT_MSG="ST7735 Display Project - Arduino Due Implementation

Features:
- Complete ST7735 LCD display integration (158x126 usable area)
- Bitmap image reception via serial communication
- Interactive calibration tool for display boundaries
- RGB565 color format with automatic scaling
- Comprehensive bounds checking and error handling

Hardware:
- Arduino Due with ST7735 1.8\" TFT LCD
- Pin configuration: CS=7, DC=10, RST=8, BL=9
- Serial communication for image data transmission

Technical Details:
- PlatformIO build system
- Adafruit ST7735/GFX libraries
- Calibrated display origin at (1,2)
- Landscape orientation support

Author: $GIT_USERNAME <$GIT_EMAIL>"

    git commit -m "$COMMIT_MSG"
    print_success "Changes committed"
fi

# Create GitHub repository and push
print_step "Creating GitHub repository: $REPO_NAME"

# Check if repository already exists
if gh repo view "$GIT_USERNAME/$REPO_NAME" &> /dev/null; then
    print_warning "Repository $REPO_NAME already exists!"
    read -p "Do you want to push to the existing repository? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Aborted by user"
        exit 1
    fi
    
    # Add remote if it doesn't exist
    if ! git remote get-url origin &> /dev/null; then
        git remote add origin "https://github.com/$GIT_USERNAME/$REPO_NAME.git"
    fi
    
    # Push to existing repository
    git branch -M main
    git push -u origin main
    print_success "Pushed to existing repository"
else
    # Create new repository
    gh repo create "$REPO_NAME" \
        --description "$REPO_DESCRIPTION" \
        $VISIBILITY_FLAG \
        --source=. \
        --push \
        --remote=origin

    print_success "Repository created and pushed to GitHub!"
fi

# Create or update release
print_step "Creating/updating release..."
RELEASE_TAG="v1.0.0"
RELEASE_NOTES="# ST7735 Display Project - Arduino Due Implementation

## 🚀 Features
- **Complete ST7735 LCD Integration**: Full support for 160x128 display with 158x126 usable area
- **Bitmap Image Display**: Receives and displays images via serial communication
- **Interactive Calibration**: Tools for precise display boundary determination
- **Automatic Image Processing**: RGB565 format with scaling and centering
- **Robust Error Handling**: Comprehensive bounds checking and validation

## 🔧 Hardware Requirements
- ST7735 1.8\" TFT LCD Display (160x128 pixels)
- Arduino Due microcontroller
- Raspberry Pi (for image processing and transmission)
- USB cable for serial communication

## 📊 Technical Specifications
- **Display Area**: 158x126 usable pixels (origin at 1,2)
- **Color Format**: RGB565
- **Communication**: Serial over USB (115200 baud)
- **Orientation**: Landscape with automatic rotation handling

## 🛠 Pin Configuration
- CS (Chip Select): Pin 7
- DC (Data/Command): Pin 10  
- RST (Reset): Pin 8
- BL (Backlight): Pin 9

## 📁 Project Structure
- \`src/main.cpp\` - Primary bitmap display receiver
- \`tools/cal_lcd.cpp\` - Interactive calibration utility
- \`platformio.ini\` - PlatformIO build configuration

## 🚀 Quick Start
1. Upload Arduino code: \`platformio run --target upload\`
2. Run image sender on Raspberry Pi: \`python3 bitmap_sender.py image.png\`

## 🔬 Calibration Results
Through interactive testing, determined optimal display settings:
- Usable area: 158x126 pixels
- Origin offset: (1,2) to avoid border artifacts
- Frame boundaries validated for perfect image display

Built with PlatformIO and Adafruit libraries by $GIT_USERNAME"

# Check if release exists and delete it first
if gh release view "$RELEASE_TAG" &> /dev/null; then
    print_info "Updating existing release..."
    gh release delete "$RELEASE_TAG" --yes || true
fi

gh release create "$RELEASE_TAG" \
    --title "ST7735 Display Project v1.0.0 - Arduino Due Implementation" \
    --notes "$RELEASE_NOTES" \
    || print_warning "Release creation failed"

# Generate final summary
echo
echo "=========================================="
echo "🎉 PROJECT PUBLISHED SUCCESSFULLY!"
echo "=========================================="
echo
print_success "Repository URL: https://github.com/$GIT_USERNAME/$REPO_NAME"
print_success "Clone URL: git clone https://github.com/$GIT_USERNAME/$REPO_NAME.git"
echo
print_info "📋 Repository Contents:"
echo "  • Arduino Due source code with ST7735 display integration"
echo "  • Interactive calibration tools"
echo "  • Comprehensive documentation and README"
echo "  • PlatformIO configuration for easy building"
echo
print_info "🔄 Development Workflow:"
echo "  • git add . && git commit -m 'Your changes' && git push"
echo "  • platformio run --target upload  # Upload to Arduino"
echo "  • gh release create v1.1.0 --notes 'Release notes'  # New release"
echo
echo "📱 Hardware Setup:"
echo "  • Connect ST7735 to Arduino Due (CS=7, DC=10, RST=8, BL=9)"
echo "  • Upload code with PlatformIO"
echo "  • Use Raspberry Pi for image transmission"
echo
print_success "🚀 Your ST7735 project is now live on GitHub!"

# Open repository in browser (optional)
read -p "Would you like to open the repository in your browser now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh repo view "$REPO_NAME" --web
fi

print_success "✨ Setup complete! Happy coding!"