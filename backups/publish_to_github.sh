#!/bin/bash

# ST7735 Display Project - GitHub Repository Publisher
# Author: grusboyd
# Date: October 5, 2025

set -e  # Exit on any error

echo "=========================================="
echo "ST7735 Project - GitHub Repository Publisher"
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

# Function to check if GitHub CLI is installed
check_gh_cli() {
    if command -v gh &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to install GitHub CLI
install_gh_cli() {
    print_step "Installing GitHub CLI..."
    
    # Check if we're on Raspberry Pi/Debian/Ubuntu
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y curl
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install -y gh
    else
        print_error "Automatic GitHub CLI installation not supported on this system."
        print_info "Please install GitHub CLI manually from: https://github.com/cli/cli#installation"
        print_info "Then run this script again."
        exit 1
    fi
}

# Function to copy existing project files
copy_existing_files() {
    local source_arduino="$1"
    local source_python="$2"
    local target_dir="$3"
    
    print_step "Copying existing project files..."
    
    # Copy Arduino code
    if [ -d "$source_arduino" ]; then
        print_info "Copying Arduino code from: $source_arduino"
        cp -r "$source_arduino"/* "$target_dir/arduino_code/" 2>/dev/null || true
        
        # Ensure we preserve the platformio.ini we want
        if [ -f "$source_arduino/platformio.ini" ]; then
            cp "$source_arduino/platformio.ini" "$target_dir/arduino_code/"
        fi
        
        print_success "Arduino code copied"
    fi
    
    # Copy Python code
    if [ -d "$source_python" ]; then
        print_info "Copying Python code from: $source_python"
        cp "$source_python"/* "$target_dir/raspberry_pi_code/" 2>/dev/null || true
        print_success "Python code copied"
    fi
    
    # Copy test images if they exist
    local test_images_source="$source_python/../test_images"
    if [ -d "$test_images_source" ]; then
        print_info "Copying test images..."
        cp -r "$test_images_source"/* "$target_dir/test_images/" 2>/dev/null || true
        print_success "Test images copied"
    fi
}

# Main script starts here
print_step "Checking prerequisites..."

# Check if git is configured
if ! git config --global user.name &> /dev/null; then
    print_info "Configuring Git user settings..."
    git config --global user.name "$GIT_USERNAME"
    git config --global user.email "$GIT_EMAIL"
fi

# Check for GitHub CLI
if ! check_gh_cli; then
    print_warning "GitHub CLI (gh) is not installed."
    read -p "Would you like to install it automatically? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_gh_cli
    else
        print_error "GitHub CLI is required for automatic repository creation."
        print_info "Please install it manually: https://github.com/cli/cli#installation"
        exit 1
    fi
fi

# Get project path
read -p "Enter the path to your ST7735_Display_Project directory (or press Enter to browse): " PROJECT_PATH

if [ -z "$PROJECT_PATH" ]; then
    # Show available projects
    print_info "Available project directories:"
    find /home/boyd/Documents/PlatformIO/Projects -maxdepth 2 -name "*ST7735*" -type d 2>/dev/null || true
    echo
    read -p "Enter the full path to your project: " PROJECT_PATH
fi

# Validate project path
if [ ! -d "$PROJECT_PATH" ]; then
    print_error "Project directory does not exist: $PROJECT_PATH"
    exit 1
fi

if [ ! -f "$PROJECT_PATH/.git/config" ]; then
    print_error "Not a git repository. Please run the setup_repository.sh script first."
    exit 1
fi

cd "$PROJECT_PATH"

# Get repository name
read -p "Enter GitHub repository name (default: $DEFAULT_REPO_NAME): " REPO_NAME
REPO_NAME=${REPO_NAME:-$DEFAULT_REPO_NAME}

# Get repository description
read -p "Enter repository description (optional): " REPO_DESCRIPTION
REPO_DESCRIPTION=${REPO_DESCRIPTION:-"ST7735 LCD Display Project with Arduino Due and Raspberry Pi - Bitmap image transmission and display system"}

# Ask about copying existing files
echo
print_info "Do you want to copy files from your existing project?"
read -p "Copy existing Arduino code? Enter path (or press Enter to skip): " ARDUINO_SOURCE
read -p "Copy existing Python code? Enter path (or press Enter to skip): " PYTHON_SOURCE

if [ ! -z "$ARDUINO_SOURCE" ] || [ ! -z "$PYTHON_SOURCE" ]; then
    copy_existing_files "$ARDUINO_SOURCE" "$PYTHON_SOURCE" "$PROJECT_PATH"
fi

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

# Check GitHub CLI authentication
print_step "Checking GitHub authentication..."
if ! gh auth status &> /dev/null; then
    print_info "You need to authenticate with GitHub."
    print_info "This will open a web browser for authentication."
    read -p "Press Enter to continue..."
    gh auth login
fi

print_success "GitHub authentication verified"

# Add and commit any new files
print_step "Adding and committing current changes..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    print_info "No changes to commit"
else
    git commit -m "Update project files

- Added existing Arduino and Python code
- Updated project structure
- Prepared for GitHub publication

Committed by: $GIT_USERNAME <$GIT_EMAIL>"
    print_success "Changes committed"
fi

# Create GitHub repository
print_step "Creating GitHub repository: $REPO_NAME"
gh repo create "$REPO_NAME" \
    --description "$REPO_DESCRIPTION" \
    $VISIBILITY_FLAG \
    --source=. \
    --push \
    --remote=origin

print_success "Repository created and pushed to GitHub!"

# Set up branch protection (optional for public repos)
if [ "$REPO_TYPE" = "1" ]; then
    print_step "Setting up basic branch protection..."
    gh api repos/$GIT_USERNAME/$REPO_NAME/branches/main/protection \
        --method PUT \
        --field required_status_checks='{"strict":false,"contexts":[]}' \
        --field enforce_admins=false \
        --field required_pull_request_reviews=null \
        --field restrictions=null \
        --silent || print_warning "Branch protection setup failed (this is optional)"
fi

# Create initial release
print_step "Creating initial release..."
RELEASE_TAG="v1.0.0"
RELEASE_NOTES="# ST7735 Display Project - Initial Release

## Features
- Complete ST7735 LCD display integration with Arduino Due
- Raspberry Pi image processing and transmission
- Interactive calibration tools
- Comprehensive bounds checking and error handling
- RGB565 color format support
- Automatic image scaling and centering

## Hardware Requirements
- ST7735 1.8\" TFT LCD Display (160x128 pixels)
- Arduino Due
- Raspberry Pi (for image processing)

## Quick Start
1. Upload Arduino code using PlatformIO
2. Run Python image sender on Raspberry Pi
3. See README.md for detailed instructions

## Project Structure
- \`arduino_code/\` - PlatformIO project for Arduino Due
- \`raspberry_pi_code/\` - Python scripts for image processing  
- \`test_images/\` - Sample images for testing
- \`docs/notebooks/\` - Documentation and analysis

Built by: $GIT_USERNAME"

gh release create "$RELEASE_TAG" \
    --title "ST7735 Display Project - Initial Release" \
    --notes "$RELEASE_NOTES" \
    || print_warning "Release creation failed (repository might already have releases)"

# Generate project summary
echo
echo "=========================================="
echo "PROJECT PUBLISHED SUCCESSFULLY!"
echo "=========================================="
echo
print_success "Repository URL: https://github.com/$GIT_USERNAME/$REPO_NAME"
print_success "Clone URL: git clone https://github.com/$GIT_USERNAME/$REPO_NAME.git"
echo
print_info "Next steps:"
echo "1. Visit your repository: gh repo view $REPO_NAME --web"
echo "2. Add a detailed README with setup instructions"
echo "3. Add more test images and documentation"
echo "4. Consider adding GitHub Actions for CI/CD"
echo
echo "Useful commands for ongoing development:"
echo "• git add . && git commit -m 'Your message' && git push"
echo "• gh issue create --title 'Issue title' --body 'Issue description'"
echo "• gh pr create --title 'PR title' --body 'PR description'"
echo "• gh release create v1.1.0 --title 'Release title' --notes 'Release notes'"
echo
print_success "Project setup complete! Happy coding! 🚀"

# Open repository in browser (optional)
read -p "Would you like to open the repository in your browser now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh repo view "$REPO_NAME" --web
fi