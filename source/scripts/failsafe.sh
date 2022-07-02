#!/bin/bash
/usr/sbin/iptables -P INPUT ACCEPT
/usr/sbin/iptables -P OUTPUT ACCEPT
/usr/sbin/iptables -P FORWARD ACCEPT
/usr/sbin/iptables -F INPUT
/usr/sbin/iptables -F FORWARD
/usr/sbin/iptables -F OUTPUT
/usr/sbin/iptables -t nat -F PREROUTING
/usr/sbin/iptables -t nat -F POSTROUTING
