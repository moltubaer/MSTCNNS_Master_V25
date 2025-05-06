#!/bin/bash

# List of container names or IDs
containers=("free5gc_amf" "free5gc_smf" "free5gc_upf" "free5gc_udm" "free5gc_ausf" "free5gc_pcf" "free5gc_nssf" "free5gc_udr" "free5gc_nrf")


# Loop through each container
for container in "${containers[@]}"; do
    echo "Installing tcpdump in container: $container"
    
    docker exec "$container" sh -c "apk update && apk add --no-cache tcpdump"

    if [ $? -eq 0 ]; then
        echo "tcpdump installed successfully in $container"
    else
        echo "Failed to install tcpdump in $container"
    fi

    echo ""
done
