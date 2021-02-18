import openpyxl
import os
import re
import sys
import time
import netmiko
import paramiko
from netmiko import ConnectHandler

from cisco_connect import CiscoConnect

timeStamp = time.strftime("__[%Y.%b.%d].[%I.%M.%S.%p]")

device_type = "cisco_ios"
username = "net-auto"
    # input('Enter the username: ')
password = "N3t.@u701820"
    # input('Enter the password: ')
ip = "10.0.2.64"
    # input('Enter the seed device IP: ')
command = "show cdp neighbors detail | in Device ID:.+\\.com|IP address:|Platform|Version"

match_set = {""}
ips_list = []
device_names_list = []
dev_obj = None

def connect_to_dev (dev_ip):
    if dev_ip not in ips_list:
        ips_list.append(dev_ip)
        dev_obj = CiscoConnect(device_type, dev_ip, username, password)
        connection = dev_obj.connect()
        if connection is None:
            dev_obj = None
        return dev_obj

def find_subinterfaces_matches(dev_object):
    int_br_cmd = 'sh ip inter br | in ^[^ ]+\\.[0-9]+.+up.+up'
    int_br_cmd_output = dev_object.send_cmnd(int_br_cmd)
    regex = '''(?:\S+\.\d+\s+\d+\.\d+\.\d+\.\d+)'''
    pattern = re.compile(regex)
    matches = pattern.findall(int_br_cmd_output)
    # print(matches)
    matches = set(matches)
    if len(matches) < 1:
        print("\nDevice ID: {}".format(dev_object.device_name))
        print(" IP address: " + dev_object.device_ip)
        print(" Note: I don't have any sub-interfaces in up up state")
    else:
        for m in matches:
            match_pices = str.split(m)
            # print(match_pices[0])
            sh_ip_arp_output = dev_object.send_cmnd("sh ip arp " + match_pices[0])
            regex = '''(\d+\.\d+\.\d+\.\d+)\s+\d+'''
            pattern = re.compile(regex)
            arp_matches = pattern.findall(sh_ip_arp_output)
            if len(arp_matches) < 1:
                print("\nDevice ID: {}".format(dev_object.device_name))
                print(" IP address: " + dev_object.device_ip)
                print(" Note: Currently, the network device connected to \"" + match_pices[0] + "\" is down")
            else:
                for i in arp_matches:
                    # print(m)
                    dev_obj = connect_to_dev(i)
                    if dev_obj is not None:
                        check_find(dev_obj)

def find_cdp_matches (device_name, cdp_cmd_output, device_ip):
    regex = '''(Device ID: .+\s+IP address:\s+\d+\.\d+\.\d+\.\d+\s*Platform:.+\s*Capabilities:.+\s*Version :\s*.+Version \S+)'''
    pattern = re.compile(regex)
    matches = pattern.findall(cdp_cmd_output)
    matches = set(matches)
    if len(matches) < 1:
        print("\nDevice ID: {}".format(device_name))
        print(" IP address: " + device_ip)
        print(" Note: My CDP Neighbor list is empty")
    else:
        for match in matches:
            match = re.sub('\.\w+\.com', '', match)
            match = re.sub('(Platform:\s*.+),\s*(Capabilities:\s*.+)', '  \\1\n  \\2', match)
            match = re.sub('(Version :)\n(.+),', '  \\1 \\2', match)
            match_lines_list = str.splitlines(match)
            new_match_dev_id = re.findall(re.compile('Device ID: \S+$'), match_lines_list[0]).pop()
            if match not in match_set and new_match_dev_id not in str(match_set):
                match_set.add(match)
                device_ip = re.findall(re.compile('\d+\.\d+\.\d+\.\d+'), match_lines_list[1])
                dev_obj = connect_to_dev(device_ip.pop())
                if dev_obj is not None:
                    check_find(dev_obj)

def check_find(dev_object):
    device_name = dev_object.device_name
    device_ip = dev_object.device_ip
    if device_name not in device_names_list:
        device_names_list.append(device_name)
        if device_name.__contains__("ASR"):
            find_subinterfaces_matches(dev_object)
        cmd_output = dev_object.send_cmnd(command)
        if len(cmd_output.strip()) > 1:
            dev_object.disconnect()
            find_cdp_matches(device_name, cmd_output, device_ip)

def print_matches():
    for m in sorted(match_set):
        print('\n'+m)
    sys.stdout.close()

if __name__ == '__main__':
    sys.stdout = open('matches_set@' + str(timeStamp) + ".txt", 'w')
    dev_obj = connect_to_dev(ip)
    if dev_obj is not None:
        check_find(dev_obj)
    print_matches()