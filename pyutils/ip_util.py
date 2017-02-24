# -*- coding:utf-8 -*-

from .data import ip_2_int

def same_net(ip1, ip2, netmask):
    '''
        check if these two IP in the same subnet.
        input:
            ip1, ip2 : display string. e.g.: '192.168.2.33' or int
            netmask : display string. e.g.: '255.255.255.0' or int
    '''
    ip1 = ip_2_int(ip1)
    ip2 = ip_2_int(ip2)
    netmask = ip_2_int(netmask)

    return ip1 & netmask == ip2 & netmask

