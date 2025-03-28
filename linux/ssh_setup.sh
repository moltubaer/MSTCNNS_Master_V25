#!/bin/bash

# Copy this script to vm
# scp startScript.sh ubuntu@<IP_ADDRESS>:/home/ubuntu/

# Initial updates  and installation of packets
echo "Updating the system..."
sudo apt-get update && sudo apt-get upgrade -y
echo "Installing essential packages..."
sudo apt-get install -y curl wget git vim htop net-tools unzip

# Change to norwegian keyboard
sudo loadkeys no

# Install OpenSSH Server if not already installed
if ! dpkg -l | grep -q openssh-server; then
  echo "Installing OpenSSH Server..."
  sudo apt update && sudo apt install -y openssh-server
fi

# Variables
SSH_USER="ubuntu" # Default user (adjust if needed)
SSH_KEY1="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDSOEhyJ6KPA8dA8ySKhHRpbNMIdnIq5jSg7JiaBzoQlbGHv/miUun0GOsFjbLq42Iv8YWbQGQh4NpSklwF4yrW3Iw2KzRhK52ns9jnAHqygXDiE3hNykspbj+LDlR0aCKelUlpoINYfWJRJRr9YRYIKTo43fTIek8Ehx3eGrbPYyDcBGt9ZYHct+doiWyWtKronsOWp+5QBljXnDC5i31IO6me96hRvLmPrJuSa+Nh6DbnqBjz3VBf/Y/0l61ocCku8iSS0HrOoh8GPzQOzFRGGIUZzcM27Yb2YezPsle+VHVuylpeD59f5Y5PcPI9QMAXsRe6xBO8SjtPOBIDAZ1ZWPI5zT+DqITTAZvyIFfl+KMgPQTEnt9rVBo9g3g90Qr9QcMEGwkLyGQuGxhxguCLAWKACH76XAt0bYyGSi7/GoFPeM8WMFnnff/R9KGr28/WNr7+Lxhq0V4Xg9Q4CJJO2AYCQwhBFDjve0j7B8ixTpKvYvMQ2rUp80uRk6hJ8tc= alexamol@alexamol-UX430UQ"
SSH_KEY2="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDi4Ojq9zoethDBm9aJfUshKMePIHhxe4ZSHjv4N/LqHkiB74vf5v2Q/x+0iBa9lIydb/StK8DFUvDPQTxC2J1va1K9BQsR/LHV3w3G/dSycWT8W8E2jhtAVIoMtr0I+WFggaL0hn0t+LNGUljA0nSo+mu2ahTcl4TO9bPFmilf4tGZLN3KPeEifUq5vkHyZTy6Stjf9ZCBTjZIUl91MQMT0wPugLPHEOce6uwVf80rLQHh8Ybn1eQt4u4o2wE3X4dmQd8rr6lwNGSJSr5sSCEhztGL7rWzevq1rVVXjOXOB8AfsAemKv0LxD0z4KyiJEnouFu1JyirntpXeQbzBOfRcFZkUx30RAnKrVCkL6wJsvGJfjB6+BXmYS6cRGklidb7N+69fvTNT0yrXsINCENpcomrktz6VsK8DHIrAjuyz+MFi+lujPdU3l9bpaSqotxu8jUzPU6eXhJnHBAMDw+J6k14jMw0yNR40iDAY7o4mp7OpkeXGQnwKFcAQC4Y7ec= marcusjohannessen@dhcp-10-22-31-1.wlan.ntnu.no"
SSH_DIR="/home/$SSH_USER/.ssh"
AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"

# Create the .ssh directory if it doesn't exist
if [ ! -d "$SSH_DIR" ]; then
  echo "Creating $SSH_DIR..."
  mkdir -p "$SSH_DIR"
  chown $SSH_USER:$SSH_USER "$SSH_DIR"
  chmod 700 "$SSH_DIR"
fi

# Add the first public key to authorized_keys
if ! grep -q "$SSH_KEY1" "$AUTHORIZED_KEYS" 2>/dev/null; then
  echo "Adding first public key to $AUTHORIZED_KEYS..."
  echo "$SSH_KEY1" >> "$AUTHORIZED_KEYS"
else
  echo "First public key already exists in $AUTHORIZED_KEYS."
fi

# Add the second public key to authorized_keys
if ! grep -q "$SSH_KEY2" "$AUTHORIZED_KEYS" 2>/dev/null; then
  echo "Adding second public key to $AUTHORIZED_KEYS..."
  echo "$SSH_KEY2" >> "$AUTHORIZED_KEYS"
else
  echo "Second public key already exists in $AUTHORIZED_KEYS."
fi

# Set correct permissions
chown $SSH_USER:$SSH_USER "$AUTHORIZED_KEYS"
chmod 600 "$AUTHORIZED_KEYS"

# Ensure SSH service is running
echo "Ensuring SSH service is running..."
sudo systemctl enable ssh
sudo systemctl restart ssh

# Output completion message
echo "SSH configuration completed for user $SSH_USER."
