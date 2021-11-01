# eos-scripts
## get_ip.sh
Find the IP address associated with the given interface. Usage:
    ```get_ip.sh eth?```

## test_interfaces.py
Script to test WAN uplinks by pinging the configured IP addresses through each configured interface.
Configuration for this script should be stored in `test_interfaces.config.json` in the same directory.
* For each connection, ping each of the configured IP addresses.
* If two of the three IPs are inaccessible for the given connection, add it to the list of connections which need to be retried.
* Wait 5 seconds, and then retry the failed connections.
* If two of the three IPs are still inaccessible for the given connection, add it to the list of connections which need a notification.
* Send an email notifying the user of which connections are down.
