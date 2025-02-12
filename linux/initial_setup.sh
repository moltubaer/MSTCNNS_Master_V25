#!/bin/bash

# Cloning project repo
sudo apt-get update
sudo apt-get install -y git
echo "Installing git"
cd ~
git clone https://github.com/moltubaer/MSTCNNS_Master_V25.git

# Installing ubuntu server packages
sudo apt update
sudo apt install -y ubuntu-server

sudo apt autoremove -y
sudo apt clean

