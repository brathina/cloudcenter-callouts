#!/home/cliqruser/callout/bin/python
import os
import uuid
import logging
import pprint
logging.basicConfig(
    filename = '/usr/local/cliqr/callout/vmname/vmname.log',
    format = "%(levelname)s:{job_name}:%(message)s".format(
        job_name=os.getenv('eNV_parentJobName')
    ),
    level = logging.DEBUG
)

logging.debug(pprint.pformat(dict(os.environ), indent=2))

username = os.getenv('eNV_launchUserName').split("_")[0]
# job_name = os.getenv('eNV_parentJobName')
job_name = "".join(a for a in os.getenv('eNV_parentJobName') if (a.isalnum())).lower()
# tier_name = os.getenv('eNV_cliqrAppTierName')
tier_name = "".join(a for a in os.getenv('eNV_cliqrAppTierName') if (a.isalnum())).lower()
os_type = os.getenv('eNV_osName')

uuid = uuid.uuid4().hex  # Use hex just to get rid of the hyphens.

# Windows names have to be shorter for NetBOIS legacy reasons.
if os_type == "Windows":
    name = "{job_name}-{tier_name}-{uuid}".format(
        job_name=job_name[:5],
        tier_name=tier_name[:5],
        uuid=uuid
    )[:14]
else:
    name = "{job_name}-{tier_name}-{uuid}".format(
        job_name=job_name[:8],
        tier_name=tier_name[:8],
        uuid=uuid
    )[:24]

print("vmName={name}".format(name=name))