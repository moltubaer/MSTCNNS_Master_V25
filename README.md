# MSTCNNS Master Project (Spring 2025)

This repository contains the code, scripts, and configuration used for the master’s thesis project on performance testing of open-source 5G core networks. It implements a platform-agnostic, test-driven framework for measuring control-plane latency and resource usage under various traffic patterns. The artifacts include deployment manifests, test automation scripts, packet-capture and parsing tools, and data-analysis notebooks.

## Repository Structure

- **Open5GS/**  
  Deployment manifests and related scripts for launching and configuring the Open5GS 5G core. Contains Docker Compose files or other provisioning scripts needed to set up Open5GS in the testbed environment.

- **free5gc-compose/**  
  Docker Compose files and configuration scripts for deploying Free5GC. Used to spin up the Free5GC core for baseline and additional tests.

- **ueransim/**  
  Configuration and scripts for UERANSIM, the RAN emulator used to generate UE registration and session-establishment workloads. Includes config files specifying the number of UEs, inter-arrival parameters, and other RAN settings.

- **capture_scripts/**  
  Packet-capture and parsing utilities. Contains `tshark` filter definitions, scripts to extract control-plane messages, convert PCAP to CSV/PDML, and any helpers for timestamp alignment and PCT computation.

- **test_scripts/**  
  Automation scripts to launch specific test cases against a given 5GC implementation. These may handle parameterization (e.g., UE count, inter-arrival pattern), orchestration of UERANSIM, triggering captures, and collecting raw results.

- **data_analysis/**  
  Jupyter notebooks or Python scripts that process raw output into statistics and visualizations. Includes code to compute end-to-end PCT distributions, per-NF breakdowns, time-series plots, box plots, CDFs, and CPU/memory usage charts.

- **linux/**  
  Host-configuration scripts and tuning parameters (e.g., sysctl settings, CPU affinity, kernel options) used to prepare the test VM or machine. Ensures consistent environment and isolates variables across runs.

- **core_workflow.sh**  
  A top-level orchestration script that ties together deployment, workload generation, capture, and analysis steps to run a full experiment pipeline end-to-end.


