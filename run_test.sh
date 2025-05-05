#!/bin/bash

declare -A aether
aether[ssh-connection]="ubuntu@10.100.51.81"
aether[name]="onf aether"

echo "${aether[name]}"