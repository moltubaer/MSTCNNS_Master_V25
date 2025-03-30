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
SSH_KEY1="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDlNtRQUJTU94sRGu+YrG2MENhE6HvH7HflUG75QWEvhYy9//YZxu6mbLxGDLN0/KQfI5u8lswcpF0N6hcp/J8epNqJ17tCCumCumAlyvBPiahmALSI7X5CcCKgVc4Y5Jp/ilMoVAXH6Dnli/+gPogH+t+hz3vTlmo8/ubq2AnGfCTpBPkd1Y3RiZpTLTLRTF7CSn6px6w0Qm2UEyH4xcRJ0uJCMAo3+8IB7iskV6e+3fzSzu2iXaHLAHhHX4SHOcu898d8fZmUI8hHXXTs9Q827HTunMRfb8O9Uj+in672GBxKN0/zdLEyOuQoXEw3LMAqVQyWK9b1IYd7LnCQw6qVdTJb7yE+aJVeKnwfM9/bxhPB1QbjZe9tL5cDDMpba+HbIf7HFzYxnSukKG5gCxyc06yxm2/FDQ0eBXy2njy7RGVrwzbV6xeQkl67Rs8Z4gNrmMVwWaLxbXlUA6gJhfSHFeneWazHqQYQdtjeBPYDFJAjpINr0hjFf5XkGwTlc70= alexandermoltu@pop-os"
SSH_KEY2="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDZ7kgm/BStL3pERReASrbNGGsPFTVp84Z8xYWHCw+qA3RJeZyu9KUubI9KW+ZXKiSKs1vs2GlS2LoD26RF1NKZ6KG5K7TzpUBBmnmI/BUvwkckBPxAIDD5K7YefbhnCl2gvaMF1pi33u39o4fDYcVNpcM3UW2LZskSW6vRXb5q8sPKhcYzeXUZ37dAO+GkWCXxmn3VJgUm6m3zx4o+oAc20rXBMLVeCOpYQ9N7h9Slb9TX8AI2AOUmzZnNJ2rVt7dVNPmSkfyeHeU324paqRnYB+6gbLXZhC2MknhATe+nw9I3iO649B3CjUjJ89SRk/k9lbCTfYQpOb1UdveSR2R/ marcusjohannessen@dhcp-10-22-28-196.wlan.ntnu.no"
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
