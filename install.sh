#!/bin/bash
# vim-dashboard installation script for Unix/Linux/macOS
# This script sets up the virtual environment and installs dependencies

set -e  # Exit on any error

echo "vim-dashboard Installation Script for Unix/Linux/macOS"
echo "====================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python 3 is available
PYTHON_CMD=""
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    # Check if it's Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3 not found. Please install Python 3.7 or later."
    echo "On Ubuntu/Debian: sudo apt-get install python3 python3-venv"
    echo "On CentOS/RHEL: sudo yum install python3 python3-venv"
    echo "On macOS: brew install python3"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Make install.py executable if it isn't already
chmod +x install.py

# Run the Python installation script
$PYTHON_CMD install.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Installation completed successfully!"
else
    echo "Installation failed!"
    exit 1
fi