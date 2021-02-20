import re
import sys
import time

from cisco_connect import CiscoConnect

timeStamp = time.strftime("__[%Y.%b.%d].[%I.%M.%S.%p]")

device_type = "cisco_ios"
username = input('Enter the username: ')
password = input('Enter the password: ')
ip = input('Enter the seed device IP: ')

match_set = {""}
ips_list = []
device_names_list = []
dev_obj = None

def connect_to_dev (dev_ip):
    if dev_ip not in ips_list:
        ips_list.append(dev_ip)
        dev_obj = CiscoConnect(device_type, dev_ip, username, password)
        if dev_obj.connect() is not None:
            check_find(dev_obj)

def find_subinterfaces_matches(dev_object):
    int_br_cmd = 'sh ip inter br | in ^[^ ]+\\.[0-9]+.+up.+up'
    int_br_cmd_output = dev_object.send_cmnd(int_br_cmd)
    regex = '''(?:\S+\.\d+\s+\d+\.\d+\.\d+\.\d+)'''
    matches = find_regex(regex, int_br_cmd_output)
    if len(matches) < 1:
        msg = " Note: I don't have any sub-interfaces in up up state"
        no_match_msg(dev_object.device_name, dev_object.device_ip, msg)
    else:
        for m in matches:
            # To split the sub-interface name from it's IP address.
            match_pices = str.split(m)
            sh_ip_arp_output = dev_object.send_cmnd("sh ip arp " + match_pices[0])
            regex = '''(\d+\.\d+\.\d+\.\d+)\s+\d+'''
            arp_matches = find_regex(regex, sh_ip_arp_output)
            if len(arp_matches) < 1:
                msg = " Note: Currently, the network device connected to \"" + match_pices[0] + "\" is down"
                no_match_msg(dev_object.device_name, dev_object.device_ip, msg)
            else:
                for i in arp_matches:
                    connect_to_dev(i)

def find_cdp_matches (dev_object):
    cdp_command = "show cdp neighbors detail | in Device ID:.+\\.com|IP address:|Platform|Version"
    cdp_cmd_output = dev_object.send_cmnd(cdp_command)
    dev_object.disconnect()
    regex = '''(Device ID: .+\s+IP address:\s+\d+\.\d+\.\d+\.\d+\s*Platform:.+\s*Capabilities:.+\s*Version :\s*.+Version \S+)'''
    matches = find_regex(regex, cdp_cmd_output)
    if len(matches) < 1:
        msg = " Note: My CDP Neighbor list is empty"
        no_match_msg(dev_object.device_name, dev_object.device_ip, msg)
    else:
        for match in matches:
            match = re.sub('\.\w+\.com', '', match)
            match = re.sub('(Platform:\s*.+),\s*(Capabilities:\s*.+)', '  \\1\n  \\2', match)
            match = re.sub('(Version :)\n(.+),', '  \\1 \\2', match)
            match_lines_list = str.splitlines(match)
            new_match_dev_name = find_regex('Device ID: \S+$', match_lines_list[0]).pop()
            # To add only one match for each device,
            # (if would like to list the same device with it's different IP address remove the second condtion)
            if match not in match_set and new_match_dev_name not in str(match_set):
                match_set.add(match)
                device_ip = find_regex('\d+\.\d+\.\d+\.\d+', match_lines_list[1])
                connect_to_dev(device_ip.pop())

def check_find(dev_object):
    device_name = dev_object.device_name
    if device_name not in device_names_list:
        device_names_list.append(device_name)
        if device_name.__contains__("ASR"):
            find_subinterfaces_matches(dev_object)
        find_cdp_matches(dev_object)

def find_regex(regex_pattern, output):
    pattern = re.compile(regex_pattern)
    matches = pattern.findall(output)
    matches = set(matches)
    return matches

def no_match_msg(device_name, device_ip, msg):
    print("\nDevice ID: {}".format(device_name))
    print(" IP address: {}".format(device_ip))
    print(msg)

def print_matches():
    for m in sorted(match_set):
        print('\n'+m)
    sys.stdout.close()

if __name__ == '__main__':
    sys.stdout = open('matches_set@' + str(timeStamp) + ".txt", 'w')
    connect_to_dev(ip)
    print_matches()