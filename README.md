# Meraki Network Provisioning Script
This Python script automates the process of provisioning Meraki networks, including switches and Layer 3 configurations, by using data provided in a CSV file. It leverages the Meraki Dashboard API to create networks, claim devices, configure switch settings, setup LACP for trunk ports, and provision Layer 3 interfaces with specific VLAN configurations.

## Setup
Before running the script, ensure you have Python 3.x installed on your system. You will also need to install the requests library, which can be done via pip:

```sh
pip install requests
```
### Configuration
Environment Variables: The script uses an environment variable MERAKI_DASHBOARD_API_KEY for the Meraki API key. Ensure you set this variable in your environment:

```sh
export MERAKI_DASHBOARD_API_KEY='your_api_key_here'
```
Replace your_api_key_here with your actual Meraki Dashboard API key.

CSV File: Prepare a CSV file with the required data for provisioning your networks and devices. The expected columns are:

* SITEID
* SITEIP
* CoreSWNAME
* CoreSN
* CoreSW2PORT1-2
* AccessSW1NAME
* AccessSW1SN
* AccessSW1PORT1-2
* AccessSW2NAME
* AccessSW2SN
* AccessSW2PORT1-2
The script expects this file to be named inventory.csv by default.

Organization ID: Modify the ORGANIZATION_ID variable within the script to match your Meraki organization ID.

### Usage
To run the script, simply execute it from the command line, ensuring your CSV file is in the same directory or specifying its path if located elsewhere:

```sh
python meraki_provisioning.py
```
## Features
* __Network Creation__: Automatically creates a new network for each site listed in the CSV file.
* __Device Claiming__: Claims switches into the created networks based on their serial numbers.
* __Switch Configuration__: Configures switch settings including names, management IPs, and LACP trunk ports.
* __Layer 3 Provisioning__: Sets up Layer 3 configurations for VLANs, including SVIs and DHCP relay settings.
## Notes
Ensure your API key has adequate permissions for all operations the script performs.
Review and adjust the time zone in the network creation payload as necessary.
The script outputs logs to the console for each operation, making it easy to track the provisioning process and troubleshoot any issues.
## Licensing
https://github.com/CiscoSE/cisco-sample-code/blob/master/LICENSE