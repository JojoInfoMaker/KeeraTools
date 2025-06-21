#!/bin/bash

# Define paths
NOVA_SOURCE="$PWD/Nova-Linux-V8"
INSTALL_DIR="/opt/nova"
DESKTOP_FILE="/usr/share/applications/nova.desktop"

# Check if running with sudo/root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Check if source directory exists
if [ ! -d "$NOVA_SOURCE" ]; then
    echo "Error: Nova-Linux-V8 directory not found!"
    exit 1
fi

# Create installation directory and copy files
echo "Copying Nova files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$NOVA_SOURCE"/* "$INSTALL_DIR/"

# Set permissions
chmod -R 755 "$INSTALL_DIR"

# Create .desktop file
echo "Creating desktop entry..."
cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Name=Nova Installer
Comment=App to choose which app you want to install
Exec=$INSTALL_DIR/AppV8.py
Icon="$NOVA_SOURCE/icon.png"
Terminal=false
Type=Application
Categories=Utility;
EOL

# Set permissions for .desktop file
chmod 644 "$DESKTOP_FILE"

echo "Installation completed!"
echo "You can now find Nova Installer in your applications menu"
