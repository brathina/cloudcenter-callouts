#!/home/cliqruser/callout/bin/python
# More verbose

import requests
import os
import json
import sys
import string
import random
import netaddr
import logging

logging.basicConfig(
    filename = '/usr/local/cliqr/callout/ipam/ipam.log',
    format = "%(levelname)s:{job_name}:{vmname}:%(message)s".format(
        job_name=os.getenv('eNV_parentJobName'),
        vmname=os.getenv('vmName')
    ),
    level = logging.DEBUG
)


# requests.packages.urllib3.disable_warnings()


def vault_get_secret(path):
    s = requests.Session()

    url = "http://172.16.204.243:8200/v1/{}".format(path)

    headers = {
        'x-vault-token': "cc649599-7611-96d0-0a70-689552e6ff8b",
    }

    response = s.request("GET", url, headers=headers)
    return response.json()['data']


# ib_creds = vault_get_secret("secret/infoblox")
ib_user = "admin"  # ib_creds['username']
ib_pass = "infoblox"  # ib_creds['password']

# ad_creds = vault_get_secret("secret/activedirectory")
# ad_user = ad_creds['username']
# ad_pass = ad_creds['password']
# ad_domain = ad_creds['domain']

dep_env = os.getenv('eNV_CliqrDepEnvName', None)
os_type = os.getenv("eNV_osName")
nic_index = os.getenv("nicIndex")
image_name = os.getenv("eNV_imageName")

# Use vmname for hostname, otherwise random string.
hostname = os.getenv('vmName',
                     ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
                     )
# hostname += "nic{}".format(nic_index)

is_resource_str = os.getenv("isResourcePlacement", "false")  # Careful, these aren't booleans.
if is_resource_str == "true":
    is_resource = True
else:
    is_resource = False

domain = "ccdemolab.cisco.com"
dns_server_list = "171.70.168.183"

# Version 1.3 of the Infoblox WAPI is required to create a host record without finding
# the next available IP first, which avoids a race condition.
wapi_version = "2.6"
ib_api_endpoint = "https://10.36.60.50/wapi/v{}".format(wapi_version)
if image_name == "Windows Server 2016":
    windows_cust_spec = "mdavis2016"
elif image_name == "Windows Server 2012":
    windows_cust_spec = "mdavis2012"


linux_cust_spec = None

if is_resource:
    # Since port group is not passed in when using resource placement,
    # just assume this port group for that dep env.
    port_group = "apps-203"
else:
    port_group = os.getenv('networkId', None)


# if port_group in ['apps-201', 'apps-202']:
#    use_dhcp = True
#else:
#    use_dhcp = False
use_dhcp = False

s = requests.Session()


def get_ip_addr(ref):
    url = "{}/{}".format(ib_api_endpoint, ref)
    logging.debug(url)
    try:
        response = s.request("GET", url, verify=False, auth=(ib_user, ib_pass))
        logging.debug("Response: {}".format(response.text))
    except Exception as err:
        print("Couldn't create host record: {0}.".format(err))
        sys.exit(1)

    return response.json()['ipv4addrs'][0]['ipv4addr']


def allocate_ip():
    # Get network reference
    url = "{}/network".format(ib_api_endpoint)
    querystring = {
        "*PortGroup": port_group,
        "_return_fields": "extattrs,network"
    }
    headers = {}
    response = s.request("GET", url, headers=headers, params=querystring, verify=False,
                         auth=(ib_user, ib_pass))
    gateway = response.json()[0]['extattrs']['Gateway']['value']
    if port_group == "VM Network":
        subnet = "10.36.60.50-10.36.60.250"
    else:
        subnet = response.json()[0]['network']  # CIDR format
    netmask = str(netaddr.IPNetwork(response.json()[0]['network']).netmask)  # Convert CIDR to netmask

    # Create Host Record
    url = "{}/record:host".format(ib_api_endpoint)
    fqdn = "{hostname}nic{idx}.{domain}".format(hostname=hostname, idx=nic_index, domain=domain)
    payload = {
        "ipv4addrs": [
            {
                "ipv4addr": "func:nextavailableip:{subnet}".format(subnet=subnet)
            }
        ],
        "name": fqdn,
        "configure_for_dns": True
    }
    logging.debug(payload)
    headers = {'content-type': "application/json"}
    try:
        response = s.request("POST", url, data=json.dumps(payload), headers=headers, verify=False,
                             auth=(ib_user, ib_pass))
        logging.debug("Response: {}".format(response.text))
        logging.debug(response.status_code)
        response.raise_for_status()
        host_ref = response.json()
    except Exception as err:
        print("Response: {}".format(response.text))
        print("Couldn't create host record: {0}.".format(err))
        sys.exit(1)

    new_ip = get_ip_addr(host_ref)
    # print("Allocated IP: {}".format(new_ip))

    return {
        "ip": new_ip,
        "netmask": netmask,
        "gateway": gateway
    }


# Echo key/values back to CloudCenter for VM creation
print("nicCount=1")
print("osHostname="+hostname)

print("nicUseDhcp_0={}".format(use_dhcp))
if not use_dhcp:
    ip = allocate_ip()
    print("DnsServerList="+dns_server_list)
    print("DnsSuffixList={}".format(domain))
    print("nicIP_0={}".format(ip['ip']))
    print("nicNetmask_0={}".format(ip['netmask']))
    print("nicGateway_0={}".format(ip['gateway']))
    print("nicDnsServerList_0={}".format(dns_server_list))  # Optional


# VMWare Specific
if os_type == "Windows":
    if windows_cust_spec:
        print("custSpec=" + windows_cust_spec)
    else:
        # print("portId=asdf")  # OpenStack specific
        # Windows Specific
        print("domainAdminName={}".format(ad_user))
        print("domainAdminPassword={}".format(ad_pass))
        print("domainName={}".format(ad_domain))  # Only if joining domain.
        # print("workgroup=workgroup")
        print("organization=CliQr")
        # print("productKey=D2N9P-3P6X9-2R39C-7RTCD-MDVJX")
        # print("licenseAutoMode=")
        # print("licenseAutoModeUsers=")
        print("setAdminPassword=auslab@1")
        # print("dynamicPropertyName=")
        # print("dynamicPropertyValue=")
        print("changeSid=true")
        print("deleteAccounts=false")
        print("timeZoneId=004")
        print("fullName=MichaelDavis")
elif os_type == "Linux":
    if linux_cust_spec:
        print("custSpec=" + linux_cust_spec)
    else:
        print("domainName={}".format(domain))
        print("hwClockUTC=true")
        print("timeZone=America/Chicago")
else:
    print("Unrecognized OS Type")
    sys.exit(1)

