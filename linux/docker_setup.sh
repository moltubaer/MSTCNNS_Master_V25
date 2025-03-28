#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Update the package index
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg

# Create directory for the Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings

# Download Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set permissions for the GPG key
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker's official APT repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the package index again
sudo apt-get update

# Install Docker Engine, CLI, Containerd, Buildx, and Compose plugins
sudo apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Start and enable Docker service
sudo systemctl enable docker.service
sudo systemctl start docker.service

# Add the current user to the 'docker' group to run Docker without 'sudo'
sudo groupadd docker || true
sudo usermod -aG docker $USER

# Print completion message
echo "Docker installation completed successfully."
echo "Please log out and log back in to apply the user group changes."
