#!/bin/bash
APP_NAME=dr-mentions
BIN_NAME=dr-mentiond
INSTALL_DIR=/usr/share
BIN_DIR=/usr/bin
SERVICE_DIR=/usr/lib/systemd/user

set -e

# read -p "Are you sure you want to uninstall '$APP_NAME'? (y/N)" confirm
# shopt -s nocasematch
# if [ "$confirm"  ]
# shopt -u nocasematch

echo "Uninstalling $APP_NAME..."

if [ -e "$SERVICE_DIR/$BIN_NAME.service" ]; then
   echo "Uninstalling the $BIN_NAME.service systemd unit file..."
   rm "$SERVICE_DIR/$BIN_NAME.service"
else
   echo "No $BIN_NAME.service systemd unit file found."
fi

if [ -e "$BIN_DIR/$BIN_NAME" ]; then
   echo "Uninstalling $BIN_NAME from $BIN_DIR"
   rm "$BIN_DIR/$BIN_NAME"
else
   echo "$BIN_NAME was not found at $BIN_DIR."
fi

if [ -d "$INSTALL_DIR/$APP_NAME" ]; then
   echo "Uninstalling $INSTALL_DIR/$APP_NAME"
   rm -r "$INSTALL_DIR/$APP_NAME"
else
   echo "No $INSTALL_DIR/$APP_NAME directory to remove."
fi

echo "Uninstalled $APP_NAME"
echo "If you haven't done so yet, stop and disable the $BIN_NAME service:"
echo -e "\tsystemctl --user disable --now $BIN_NAME.service"