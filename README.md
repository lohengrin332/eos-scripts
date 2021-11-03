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

## Send mail via Gmail from an EdgeRouter
H/T to [this Q/A in the UI community forums](https://community.ui.com/questions/Email-Notification-from-EdgeRouter-for-IPs-offline-down/d96ba4ee-f139-476b-99ba-e8d7a06dbf49) for the solution.
* Create an application password in your gmail (myaccount.google.com->Security->App passwords)
* Modify `/etc/ssmtp/ssmtp.conf`:
```
root=<gmail address>@gmail.com
mailhub=smtp.gmail.com:587
UseSTARTTLS=YES
AuthUser=<gmail address>
AuthPass=<application password>
FromLineOverride=YES
```
* Modify `/etc/ssmtp/revaliases`:
```
root:<gmail address>@gmail.com:smtp.gmail.com:587
<login user>:<gmail address>@gmail.com:smtp.gmail.com:587
```

You should then be able to send an email using the command `/usr/sbin/ssmtp <recipients>`. Use `Ctrl+d` to exit and complete the message.
