#!/bin/bash

# Alpine repository config
REPO_MAIN="https://dl-cdn.alpinelinux.org/alpine/v3.15/main"
REPO_COMMUNITY="https://dl-cdn.alpinelinux.org/alpine/v3.15/community"

# Function to fix DNS
fix_dns() {
    docker exec "$1" sh -c 'echo "nameserver 1.1.1.1" > /etc/resolv.conf && echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
}

# Function to detect OS type
detect_os() {
    docker exec "$1" sh -c 'cat /etc/os-release 2>/dev/null' | grep -i -q debian && echo "debian" || echo "alpine"
}

# Function to install tcpdump
install_tcpdump() {
    container_name=$1
    echo "Configuring $container_name..."

    # Fix DNS
    fix_dns "$container_name"

    # Detect OS type
    os_type=$(detect_os "$container_name")

    if [ "$os_type" = "alpine" ]; then
        echo " -> Detected Alpine-based container"
        docker exec "$container_name" sh -c "echo '$REPO_MAIN' > /etc/apk/repositories"
        docker exec "$container_name" sh -c "echo '$REPO_COMMUNITY' >> /etc/apk/repositories"
        docker exec "$container_name" apk update
        docker exec "$container_name" apk add tcpdump
    elif [ "$os_type" = "debian" ]; then
        echo " -> Detected Debian-based container"
        docker exec "$container_name" apt update
        docker exec "$container_name" apt install -y tcpdump
    else
        echo " -> Unknown OS in $container_name. Skipping."
    fi
}

# List of containers to configure
containers=("free5gc_amf" "free5gc_smf" "free5gc_upf" "free5gc_udm" "free5gc_ausf" "free5gc_pcf" "free5gc_nssf" "free5gc_udr" "free5gc_nrf")

# Run installation
for container in "${containers[@]}"; do
    install_tcpdump "$container"
done