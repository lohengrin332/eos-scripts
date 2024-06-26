# eos-scripts
## Prereqs
### EdgeRouter
These packages require Python 2.7.9 or greater.
Make sure you have the [latest version](https://ui.com/download/software/er-4) of the EdgeRouter software.
Installation instructions are on [help.ui.com](https://help.ui.com/hc/en-us/articles/205146110-EdgeRouter-How-to-Upgrade-the-EdgeOS-Firmware).

You will also need `unzip` to extract setuptools. Install this by following [Add Debian Packages to EdgeOS v2.0.0 and Newer Versions](https://help.ui.com/hc/en-us/articles/205202560-EdgeRouter-Add-Debian-Packages-to-EdgeOS), then run `sudo apt-get install zip`.

Some of these scripts require pika to be installed on your EdgeRouter, which in turn requires Setuptools to install:
1. Install Setuptools v44.0.0 from [PyPi](https://pypi.org/project/setuptools/44.1.1/#files).
    * `sudo mkdir -p /usr/local/lib/python2.7/dist-packages ; python bootstrap.py ; sudo python setup.py install`
1. Install Pika 1.1.0 from [PyPi](https://pypi.org/project/pika/1.1.0/#files).
    * `sudo python setup.py install`

### Raspberry PI
Other scripts are designed to run on a Raspberry PI to monitor network health as a whole.
This RPI should be equipped with:
* Python v3 with `pika`
    * `sudo apt install python3-pika`
* A [Unicorn Hat HD](https://www.adafruit.com/product/3580?gad_source=1&gclid=CjwKCAjwvIWzBhAlEiwAHHWgva0qu-tcuEOzuS0iWjzK16e_SlGAjeqax0l2xw5CjxHBViT1p57GnBoCa0sQAvD_BwE)
* The unicornhathd libraries
    * `sudo apt install python3-unicornhathd`).
* [Enable SPI](https://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/)
   * `sudo raspi-config`
   * Add the user who will run the queue reader script to the `spi` group via `sudo vigr`
* Access to a RabbitMQ server:
    * `sudo apt install rabbitmq-server`
    * `sudo rabbitmq-plugins enable rabbitmq_management`
    * `sudo rabbitmqctl add_user <service user from test_interfaces.config.json> <service user password>`
    * `sudo rabbitmqctl set_permissions -p / <service user> ".*" ".*" ".*"`
    * `sudo rabbitmqctl add_user <your login user> <new password>`
    * `sudo rabbitmqctl set_user_tags <your login user> administrator`
    * `sudo rabbitmqctl set_permissions -p / <your login user> ".*" ".*" ".*"`
    * Rabbit Management console can be accessed via [http://<RPI ip>:15672/](http://192.168.1.68:15672/)

Image from Ubuntu Linux using `rpi-imager`. Install using `sudo apt install rpi-imager`. Further details [here](https://www.raspberrypi.com/software/).

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
