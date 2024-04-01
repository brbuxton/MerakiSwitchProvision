import csv
import requests
import os

# Configuration for Meraki API
API_KEY = os.getenv('MERAKI_DASHBOARD_API_KEY')  # set MERAKI_DASHBOARD_API_KEY environment variable to your key
ORGANIZATION_ID = 'your_organization_id'  # replace your_organization_id with your org_id
BASE_URL = 'https://api.meraki.com/api/v1'

headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}


def create_network(site_id):
    """
    Create a new network within the organization.
    """
    url = f'{BASE_URL}/organizations/{ORGANIZATION_ID}/networks'
    payload = {
        'name': site_id,
        'productTypes': ['switch'],
        'tags': [ "Bux"],
        'timeZone': 'America/New_York'  # Update this as needed
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()['id']
    else:
        print("Failed to create network", response.text)
        return None


def provision_switch(network_id, switch_name, switch_sn, switch_trunk_ports):
    """
    Provision a switch in the network with specific settings including name, management IP,
    and LACP trunk port aggregation.
    """

    # Claim the switch into the network
    url = f'{BASE_URL}/networks/{network_id}/devices/claim'
    payload = {'serials': [switch_sn]}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Successfully claimed switch")
    else:
        print(f"Failed to claim switch SN: {switch_sn}", response.text)

    # Update network switch general settings
    url_switch_settings = f'{BASE_URL}/devices/{switch_sn}'
    payload_switch_settings = {
        'name': switch_name,
    }

    response_switch_settings = requests.put(url_switch_settings, headers=headers, json=payload_switch_settings)
    if response_switch_settings.status_code == 200:
        print(f"Updated switch settings for {switch_name}.")
    else:
        print(f"Failed to update switch settings for {switch_name}: {response_switch_settings.text}")
        return

    # Update network switch general settings
    url_switch_ip = f'{BASE_URL}/devices/{switch_sn}/managementInterface'
    if 'access' in switch_name:
        payload_switch_ip = {
            'wan1': {
            'usingStaticIp': False,
            'vlan': 1
            }
        }
    else:
        payload_switch_ip = {
            'wan1': {
                'usingStaticIp': False,
                'vlan': 1
            }
        }

    response_switch_ip = requests.get(url_switch_ip, headers=headers, json=payload_switch_ip)
    if response_switch_ip.status_code == 200:
        print(f"Updated switch settings for {switch_sn}: {response_switch_ip.text}")
    else:
        print(f"Failed to update switch settings for {switch_sn}: {response_switch_ip.text}")
        return

    # Configure LACP trunk uplink ports
    url_link_aggregation = f'{BASE_URL}/networks/{network_id}/switch/linkAggregations'
    lacp_ports = []
    switch_trunk_ports = switch_trunk_ports.split()
    for port in switch_trunk_ports:
        print(port)
        if " " not in port:
            lacp_ports.append({'serial': switch_sn, 'portId': port})
    print(lacp_ports)
    payload_link_aggregation = {
        'switchPorts': lacp_ports
    }

    response_link_aggregation = requests.post(url_link_aggregation, headers=headers, json=payload_link_aggregation)
    if response_link_aggregation.status_code == 201:
        print(f"Configured LACP trunk ports for {switch_name}.")
    else:
        print(f"Failed to configure LACP for {switch_name}: {response_link_aggregation.text}")


def provision_layer3(switch_name, switch_ip, switch_sn, site_ip):
    """
    Provision VLANs Layer 3 SVIs in the network with specific settings
    :param network_id:
    :param switch_name:
    :param switch_ip:
    :param switch_sn:
    :return:
    """
    url_network_layer3 = f'{BASE_URL}/devices/{switch_sn}/switch/routing/interfaces'
    vlans = [1, 255, 100, 104, 105, 106, 108, 109, 111, 112, 116, 118, 120]
    # configure VLAN 255 first
    payload_vlan255 = {
        'name': f"10.{site_ip}.255.4",
        'subnet': f"10.{site_ip}.255.0/24",
        'interfaceIp': f"10.{site_ip}.255.4",
        'vlanId': 255,
        'defaultGateway': f"10.{site_ip}.255.1"
    }
    response_vlan255 = requests.post(url_network_layer3, headers=headers, json=payload_vlan255)
    if response_vlan255.status_code == 201:
        print(f"Configured SVI for {switch_name} VLAN 255.")
    else:
        print(f"Failed to configure SVI for {switch_name} VLAN 255: {response_vlan255.text}")

    for vlan in vlans:
        if vlan != 1 and vlan != 255:
            # Create an SVI with the SITEIP as second octet and VLAN as third octet with createDeviceSwitchRoutingInterface
            payload_network_layer3 = {
                "name": f"10.{site_ip}.{vlan-100}.0",
                "subnet": f"10.{site_ip}.{vlan-100}.0/24",
                "interfaceIp": f"10.{site_ip}.{vlan-100}.{switch_ip}",
                "multicastRouting": "disabled",
                "vlanId": vlan
            }
            response_network_layer3 = requests.post(url_network_layer3, headers=headers, json=payload_network_layer3)
            if response_network_layer3.status_code == 201:
                print(f"Configured SVI for {switch_name} VLAN {vlan}.")
            else:
                print(f"Failed to configure SVI for {switch_name} VLAN {vlan}: {response_network_layer3.text}")

            # Add a DHCP helper for the VLAN using updateDeviceSwitchRoutingInterfaceDhcp
            payload_dhcp = {
                "dhcpMode": "dhcpRelay",
                "dhcpRelayServerIps": ["5.5.5.5"]
            }
            try:
                url_dhcp = f'{BASE_URL}/devices/{switch_sn}/switch/routing/interfaces/{response_network_layer3.json()["interfaceId"]}/dhcp'
                response_dhcp = requests.put(url_dhcp, headers=headers, json=payload_dhcp)
                if response_dhcp.status_code == 200:
                    print(f"DHCP Relay Configured on {switch_name} VLAN {vlan}.")
                else:
                    print(f"Failed to configure DHCP on {switch_name} VLAN {vlan}: {response_dhcp.text}")
            except:
                print(f'Failed to configure DHCP on {switch_name} VLAN {vlan}. The interfaceId is invalid or not present')


    # Provision the Internet_Only ACL using updateNetworkSwitchAccessControlLists

def main(csv_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            # Create a network for each site
            print(row)
            network_id = create_network(row['SITEID'])
            if network_id:
                # Provision core switch for the created network
                provision_switch(network_id, row['CoreSWNAME'], row['CoreSN'], row['CoreSW2PORT1-2'])
                # Provision access switches for the created network
                provision_switch(network_id, row['AccessSW1NAME'], row['AccessSW1SN'], row['AccessSW1PORT1-2'])
                provision_switch(network_id, row['AccessSW2NAME'], row['AccessSW2SN'], row['AccessSW2PORT1-2'])
                # Provision Layer 3 on the Core
                provision_layer3(row['CoreSWNAME'], row['CoreSWIP'], row['CoreSN'], row['SITEIP'])



if __name__ == '__main__':
    csv_file_path = 'inventory.csv'
    main(csv_file_path)
