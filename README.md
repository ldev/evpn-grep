# evpn-grep
Webinterface for searching in EVPN-VXLAN data from Juniper IPfabrics.

Collecting data hourly via NetCONF from Juniper IP-fabric, stores it and makes it searchable. Each new data collection erases the old data.

Uses:
* PyEZ python library
* Python3
* PHP
* SQlite
* Python JSON

##
Please be aware that this is low quality code, no security what so ever has been implemented. This is more a "proof of concept" than anything that should be put into production.

## Screenshot(s)
![Screenshot from evpn-grep](documentation/screenshot-evpn-grep-2.png?raw=true)

## crontab
sqlite vacuum is used to free up space. Not ideal...
```
@hourly python3 /data/work-in-progress/evpn-grep/fetch-data-to-db.py
@hourly sqlite3 /data/work-in-progress/evpn-grep/evpn.db 'VACUUM'
```