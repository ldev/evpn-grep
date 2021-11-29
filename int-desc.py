from jnpr.junos import Device
import sys
import os

if len(sys.argv) != 3:
    print('ERROR #3')
    sys.exit()
else:
    node = sys.argv[1]
    int = sys.argv[2]
    if '.' in int:
        int = int.split('.')[0]

#
# Figure out the directory of this file
# NB: No trailing slash
#
abspath = os.path.abspath(__file__)
script_path = os.path.dirname(abspath)

#
# Gets the netconf credentials from an external file.
#
try:
    import json
    with open('/data/netconf-credentials-nginx-readable.json') as f:
        netconf_credentials = json.load(f, encoding='utf-8')
except:
    print('ERROR #4')
    sys.exit(1)

try:
    dev = Device(host=node, user=netconf_credentials['user'], password=netconf_credentials['password'], normalize=True)
    dev.open()
    int_desc_xml = dev.rpc.get_interface_information(descriptions = True, interface_name = int)

    #
    # PyEZ is returning True if desc is not found, or the interface is not found.
    #
    if int_desc_xml == True:
        print('N/A')
    else:
        if int_desc_xml.find('.//description') is not None:
            print(int_desc_xml.find('.//description').text)
        else:
            print('ERROR #1')
except Exception as e:
    print('ERROR #2')