#!/usr/bin/env python3

import json
import sys
import datetime
import os
import sqlite3
import json

from jnpr.junos import Device
from pprint import pprint
from lxml import etree

from jnpr.junos.exception import ConnectTimeoutError, ConnectUnknownHostError, RpcError

#
# Figure out the directory of this file
# NB: No trailing slash
#
abspath = os.path.abspath(__file__)
script_path = os.path.dirname(abspath)

#
# Connect to sqlite3 database
#
try:
    db_con = sqlite3.connect('%s/evpn.db' % script_path)
    db_cur = db_con.cursor()
    db_cur.execute('DROP TABLE IF EXISTS data;')
    db_con.commit()
    db_cur.execute('CREATE TABLE data (date, node, type, content);')
    db_con.commit()
    print('Connected to SQlite database "%s/evpn.db", whiped table data' % script_path)
except Exception as e:
    print(e)
    print(sys.exc_info()[0])
    print('DB error')
    sys.exit(1)

#
# Gets the netconf credentials from an external file.
#
try:
    with open('/data/netconf-credentials.json') as f:
        netconf_credentials = json.load(f, encoding='utf-8')
except:
    print('ERROR: could not load netconf credentials')
    sys.exit(1)

#
# Load hosts from hosts.json
#
try:
    with open('hosts.json') as f:
        hosts_json = json.load(f, encoding='utf-8')
        hosts = hosts_json['hosts']
except:
    print('ERROR: could not load "hosts.json"')
    sys.exit(1)


#
# Fetch data over netconf, store in DB
#
for host in hosts:
    counter = 0
    try:
        print('connecting to %s' % host)
        dev = Device(host=host, user=netconf_credentials['user'], password=netconf_credentials['password'], normalize=True)
        dev.open()

        #
        # Get all data from "show evpn database"
        #
        evpn_db = dev.rpc.get_evpn_database_information()
        for x in evpn_db:
            for entry in x.findall('mac-entry'):
                blob = []
                for tag in entry.iter():
                    if not len(tag): # checks if tags contains other tags
                        blob.append('%s: %s' % (tag.tag, tag.text))
                blargh = '\n'.join(blob)
                
                db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'EVPN database', blargh))
                counter += 1
                
        #
        # Get all data from "show ethernet-switching database"
        # 
        ethernet_table = dev.rpc.get_ethernet_switching_table_information()
        for x in ethernet_table:
            #
            # Tags (elements) to prepend to each element. E.g. bridge-domain and VLAN-ID.
            # This is information that resides outside of the inner entries (elements), and thus not accessable from the loops further down
            #
            blob_prepend = []
            
            #
            # Figure out if <l2-bridge-vlan> exists in parent element, and append it to $blob_prepend if it does.
            # This works on MX, which will show which VLAN ID (not name) a MAC entry belongs to
            #
            l2_bridge_vlan = x.find('l2-bridge-vlan')
            if l2_bridge_vlan is not None:
                l2_bridge_vlan = x.find('l2-bridge-vlan').text
                blob_prepend.append('l2-bridge-vlan: %s' % l2_bridge_vlan)
        
            #
            # QFX syntax. It uses "<l2ng-mac-entry>" elements
            #
            for entry in x.findall('l2ng-mac-entry'):
                blob = [] + blob_prepend
                for tag in entry.iter():
                    if not len(tag): # checks if tags contains other tags
                        blob.append('%s: %s' % (tag.tag, tag.text))
                db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'ethernet switching table', '\n'.join(blob)))
                counter += 1
            
            #
            # MX syntax. It uses "<l2-mac-entry>" element.
            #
            for entry in x.findall('l2-mac-entry'):
                blob = [] + blob_prepend
                for tag in entry.iter():
                    if not len(tag): # checks if tags contains other tags
                        blob.append('%s: %s' % (tag.tag, tag.text))
                db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'ethernet switching table', '\n'.join(blob)))
                counter += 1

        #
        # Get all data from "show arp no-resolve"
        # PS: There is in juniper XML output no correlation between ARP entry and routing-instance... 
        #
        arp = dev.rpc.get_arp_table_information(no_resolve = True)
        for entry in arp.findall('.//arp-table-entry'):
            blob = []
            for tag in entry.iter():
                if not len(tag): # checks if tags contains other tags
                    blob.append('%s: %s' % (tag.tag, tag.text))
            db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'ARP table', '\n'.join(blob)))
            counter += 1

        #
        # Get the data from "show configuration vlans", and prepending the keys with "conf-vlans-"
        # This only makes sense on the leaf switches (QFX)
        #
        conf_vlans = dev.rpc.get_config(filter_xml='vlans')
        for conf_vlan in conf_vlans.findall('.//vlan'):
            blob = []
            for tag in conf_vlan.iter():
                if not len(tag): # checks if tags contains other tags
                    blob.append('conf-vlans-%s: %s' % (tag.tag, tag.text))
            db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'conf-vlans', '\n'.join(blob)))
            counter += 1

        #
        # Get the data from "show configuration routing-instances VS-EVPN-DC bridge-domains", and prepending the keys with "conf-bd-"
        # This only makes sense on core routers (MX)
        #
        conf_bd = dev.rpc.get_config(filter_xml='<configuration><routing-instances><instance>VS-EVPN-DC</instance></routing-instances></configuration>')
        for conf_bd in conf_bd.findall('.//domain'):
            blob = []
            for tag in conf_bd.iter():
                if not len(tag): # checks if tags contains other tags
                    blob.append('conf-bd-%s: %s' % (tag.tag, tag.text))
            db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'conf-bd', '\n'.join(blob)))
            counter += 1

        #
        # Get data from "show ethernet-switching evpn arp-table"
        # Warning: unsupported on MX, that's why we will have to wrap this especially in try/catch
        #
        try:
            evpn_arp = dev.rpc.get_ethernet_switching_evpn_arp_table()
            for entry in evpn_arp.findall('l2ng-l2rtb-evpn-arp-entry'):
                blob = []
                for tag in entry.iter():
                    if not len(tag): # checks if tags contains other tags
                        blob.append('%s: %s' % (tag.tag, tag.text))
            pprint(blob)
            db_cur.execute("INSERT INTO data VALUES ('%s','%s', '%s', '%s')" % (datetime.datetime.now(), host, 'EVPN ARP table', '\n'.join(blob)))
            counter += 1

        except RpcError as e:
            print('Warning: %s does not support get_ethernet_switching_evpn_arp_table(). Skipping check.' % host)
            pass


        db_con.commit()
        print('%s: inserted %s rows into SQlite3 DB' % (host, counter))
    except Exception as e:
        print(e)
        print(sys.exc_info()[0])
        print('Exit due to unhandled exception')
        sys.exit(1)

print('Script finished running')