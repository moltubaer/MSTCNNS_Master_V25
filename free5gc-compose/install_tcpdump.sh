#!/bin/bash

# List of Free5GC container names from docker-compose
containers=(
  free5gc_amf
  free5gc_smf
  free5gc_upf
  free5gc_udm
  free5gc_udr
  free5gc_nrf
  free5gc_ausf
  free5gc_pcf
  free5gc_nssf
  free5gc_webui
)

for container in "${containers[@]}"; do
  echo "🔧 Installing tcpdump in $container..."

  if [[ "$container" == "free5gc_upf" ]]; then
    docker exec -u root "$container" bash -c '
      apt update && apt install -y tcpdump
    '
  else
    docker exec -u root "$container" sh -c '
      if command -v apt >/dev/null 2>&1; then
        apt update && apt install -y tcpdump
      elif command -v apk >/dev/null 2>&1; then
        apk add --no-cache tcpdump
      else
        echo "⚠️ No compatible package manager found in $container"
      fi
    '
  fi

done
