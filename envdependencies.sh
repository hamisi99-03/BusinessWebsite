#!/usr/bin/env bash

# Cross-platform setup script for Linux/macOS and Git Bash on Windows

set -e

ENV_NAME="myenv"

echo "======================================"
echo " Python Environment Setup Script"
echo "======================================"

# Detect OS
OS="$(uname -s)"

echo "Detected OS: $OS"

# -----------------------------
# Linux/macOS
# -----------------------------
if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then

    echo "Installing Python tools..."

    # Debian/Ubuntu
    if command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv

    # Fedora
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip

    # Arch Linux
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip

    else
        echo "Unsupported package manager."
        echo "Please install Python 3, pip, and venv manually."
        exit 1
    fi

    PYTHON_CMD="python3"
    ACTIVATE_CMD="source $ENV_NAME/bin/activate"

# -----------------------------
# Windows (Git Bash / MINGW)
# -----------------------------
elif [[ "$OS" == MINGW* || "$OS" == MSYS* || "$OS" == CYGWIN* ]]; then

    echo "Windows environment detected."

    # Check if Python exists
    if ! command -v python >/dev/null 2>&1; then
        echo "Python is not installed."
        echo "Download Python from:"
        echo "https://www.python.org/downloads/windows/"
        exit 1
    fi

    PYTHON_CMD="python"
    ACTIVATE_CMD="source $ENV_NAME/Scripts/activate"

else
    echo "Unsupported operating system."
    exit 1
fi

# -----------------------------
# Create Virtual Environment
# -----------------------------
echo "Creating virtual environment: $ENV_NAME"

$PYTHON_CMD -m venv $ENV_NAME

# -----------------------------
# Activate Environment
# -----------------------------
echo "Activating virtual environment..."

eval "$ACTIVATE_CMD"

# -----------------------------
# Upgrade pip
# -----------------------------
echo "Upgrading pip..."

pip install --upgrade pip

# -----------------------------
# Install Packages
# -----------------------------
echo "Installing Django, Pillow, and DRF..."

pip install django pillow djangorestframework

# -----------------------------
# Done
# -----------------------------
echo ""
echo "======================================"
echo " Setup Complete!"
echo "======================================"
echo "Virtual environment: $ENV_NAME"
echo "Installed packages:"
echo " - Django"
echo " - Pillow"
echo " - Django REST Framework"
echo ""
echo "To activate later:"
echo ""

if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    echo "source $ENV_NAME/bin/activate"
else
    echo "source $ENV_NAME/Scripts/activate"
fi