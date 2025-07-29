#!/bin/bash

echo "Nova Installer - Dependencies Setup Script"
echo "----------------------------------------"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python if not present
install_python() {
    if ! command_exists python3; then
        echo "Installing Python 3..."
        if command_exists apt; then
            sudo apt update
            sudo apt install -y python3 python3-pip
        elif command_exists dnf; then
            sudo dnf install -y python3 python3-pip
        elif command_exists pacman; then
            sudo pacman -Sy python python-pip
        else
            echo "Error: Unable to install Python. Please install Python 3 manually."
            exit 1
        fi
    fi
}

# Function to install PIL with Tk support
install_pillow_tk() {
    echo "Installing Pillow-Tk support..."
    if command_exists apt; then
        sudo apt update
        sudo apt install -y python3-pil python3-pil.imagetk
    elif command_exists dnf; then
        sudo dnf install -y python3-pillow python3-pillow-tk
    elif command_exists pacman; then
        sudo pacman -Sy python-pillow tk
    else
        echo "Attempting to install via pip..."
        pip3 install --user Pillow
        if command_exists dnf; then
            sudo dnf install -y python3-tkinter
        elif command_exists apt; then
            sudo apt install -y python3-tk
        elif command_exists pacman; then
            sudo pacman -Sy tk
        fi
    fi
}

# Function to install Flatpak for Linux
install_flatpak() {
    if ! command_exists flatpak; then
        echo "Installing Flatpak..."
        if command_exists apt; then
            sudo apt update
            sudo apt install -y flatpak
        elif command_exists dnf; then
            sudo dnf install -y flatpak
        elif command_exists pacman; then
            sudo pacman -Sy flatpak
        else
            echo "Error: Unable to install Flatpak. Please install Flatpak manually."
            exit 1
        fi
    fi
}

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)
        echo "Installing Linux dependencies..."
        install_python
        install_pillow_tk
        install_flatpak

        # Install Python packages
        pip3 install --user customtkinter
        pip3 install --user requests

        # Add Flathub repository
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

        echo "Linux dependencies installation completed!"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Installing Windows dependencies..."
        # Check if Python is installed
        if ! command_exists python3; then
            echo "Please install Python 3 from https://www.python.org/downloads/"
            echo "Make sure to check 'Add Python to PATH' during installation"
            exit 1
        fi

        # Install Python packages
        pip3 install --user customtkinter
        pip3 install --user requests
        pip3 install --user Pillow

        # Check if winget is installed
        if ! command_exists winget; then
            echo "Please ensure Windows App Installer (winget) is installed from the Microsoft Store"
            echo "or update your Windows installation to include it"
            exit 1
        fi

        echo "Windows dependencies installation completed!"
        ;;
    *)
        echo "Unsupported operating system"
        exit 1
        ;;
esac

echo ""
echo "All dependencies have been installed successfully!"
echo "You can now run Nova Installer."
