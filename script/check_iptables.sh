#!/bin/bash
mv /home/ld-sgdev/weisc/iptables /etc/sysconfig/iptables
dos2unix /etc/sysconfig/iptables
sudo service iptables restart