#!/bin/bash
APP_NAME=dr-mentions
BIN_NAME=dr-mentiond
INSTALL_DIR=/usr/share
BIN_DIR=/usr/bin
SERVICE_DIR=/usr/lib/systemd/user

set -e

echo "Installing $APP_NAME to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR/$APP_NAME"
cp -r .venv *.py "$BIN_NAME.service" icon.png uninstall.sh "$INSTALL_DIR/$APP_NAME"
chmod -R 755 "$INSTALL_DIR"

echo "Installing $BIN_NAME to $BIN_DIR..."
install -m 755 "$BIN_NAME" "$BIN_DIR/$BIN_NAME"

echo "Installing $BIN_NAME.service systemd unit file..."
cp "$BIN_NAME.service" "$SERVICE_DIR/$BIN_NAME.service"
install -m 644 "$BIN_NAME.service" "$SERVICE_DIR/$BIN_NAME.service"

echo "Done!"
echo "If this is the first time using $APP_NAME on this machine, please run '$BIN_NAME --init' and follow the instructions."
echo "To run as a service in the background and get devRant notifications run:"
echo -e "\tsystemctl --user enable --now $BIN_NAME.service"