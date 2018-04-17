#!/home/cliqruser/callout/bin/python
import os
import requests
import json
import logging

logging.basicConfig(
    filename = '/usr/local/cliqr/callout/dealloc/dealloc.log',
    format = "%(levelname)s:{job_name}:{vmname}:%(message)s".format(
        job_name=os.getenv('eNV_parentJobName'),
        vmname=os.getenv('vmName')
    ),
    level = logging.DEBUG
)

# requests.packages.urllib3.disable_warnings()


s = requests.Session()

url = "http://172.16.204.243:8200/v1/secret/infoblox"

headers = {
    'x-vault-token': "cc649599-7611-96d0-0a70-689552e6ff8b",
}

# response = s.request("GET", url, headers=headers)

# print(response.text)

ib_user = "admin"  # response.json()['data']['username']
ib_pass = "infoblox"  # response.json()['data']['password']

# print(ib_user, ib_pass)

ip_addr = os.getenv('nicIP_0')
logging.debug(ip_addr)

wapi_version = "2.6"
ib_api_endpoint = "https://10.36.60.50/wapi/v{}".format(wapi_version)


s = requests.Session()

url = "{}/ipv4address".format(ib_api_endpoint)
logging.debug(url)
querystring = {"ip_address": ip_addr}

headers = {}

response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=(ib_user, ib_pass))

logging.debug(response.text)
# Delete every object associated to this IP address.
for obj in response.json()[0]['objects']:
    url = "{}/{}".format(ib_api_endpoint, obj)
    s.request("DELETE", url, verify=False, auth=(ib_user, ib_pass))