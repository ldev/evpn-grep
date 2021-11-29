# evpn-grep
Webinterface for searching in EVPN-VXLAN data from Juniper IPfabrics.

Collecting data hourly via NetCONF from Juniper IP-fabric, stores it and makes it searchable. Each new data collection erases the old data.

Uses:
* PyEZ python library
* Python3
* PHP
* SQlite

## Screenshot(s)
![Screenshot from evpn-grep](documentation/screenshot-evpn-grep.png?raw=true)

## crontab
sqlite vacuum is used to free up space. Not ideal...
```
@hourly python3 /data/work-in-progress/evpn-grep/fetch-data-to-db.py
@hourly sqlite3 /data/work-in-progress/evpn-grep/evpn.db 'VACUUM'
```