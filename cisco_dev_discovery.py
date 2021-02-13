import openpyxl
import os
import re
import sys
import time
import netmiko
import paramiko
from netmiko import ConnectHandler

direc = 'Z:\Routing & Switching Unit\PythonCodes'
jopsDirec = 'Z:\Routing & Switching Unit\PythonCodes\JOPS'
timeStamp = time.strftime("__[%Y.%b.%d].[%I.%M.%S.%p]")

device_type = "cisco_ios"
username = input('Enter the username: ')
password = input('Enter the password: ')
ip = input('Enter the seed device IP: ')

match_set = {""}
ips_list = []
device_names_list = []

def connect (devices):
    cdp_cmd = "show cdp neighbors detail | in Device ID:.+\\.com|IP address:|Platform|Version"
    int_br_cmd = "sh ip inter br | in ^[^ ]+\\.[0-9]+.+up.+up"
    for device_para in devices:
        try:
            if device_para.get('ip') not in ips_list:
                ips_list.append(device_para.get('ip'))
                net_connect = ConnectHandler(**device_para)
                device_name = net_connect.find_prompt()
                device_ip = device_para.get('ip')
                # device_name = device_name.replace('#', '')
                if device_name not in device_names_list:
                    device_names_list.append(device_name)
                    if device_name.__contains__("ASR"):
                        int_br_cmd_output = net_connect.send_command(int_br_cmd)
                        find_subinterfaces_dev(device_name, int_br_cmd_output, device_ip, net_connect)
                    cdp_cmd_output = net_connect.send_command(cdp_cmd)
                    # print(device_name + " >> " + device_para.get('ip'))
                    find_matches(device_name, cdp_cmd_output, device_ip)
                    net_connect.disconnect()
        except paramiko.ssh_exception.AuthenticationException:
            print("\nDevice ID: \"I\'ve got an Authentication error\"")
            print(" IP address: {}".format(device_para.get('ip')))
            pass
        except netmiko.ssh_exception.NetMikoTimeoutException:
            print("\nDevice ID: \"This Device is UnReachable\"")
            print(" IP address: {}".format(device_para.get('ip')))
            pass
        except Exception as e:
            print("\nDevice ID: \"There is an Error, Maybe the command is invalid for me\"")
            print(" IP address: {}".format(device_para.get('ip')))
            print(' Error Message: \"' + str(e) + '\"')
            pass

def find_subinterfaces_dev(Device_Name, int_br_cmd_output, device_ip, net_connect):
    regex = '''(?:\S+\.\d+\s+\d+\.\d+\.\d+\.\d+)'''
    pattern = re.compile(regex)
    matches = pattern.findall(int_br_cmd_output)
    # print(matches)
    matches = set(matches)
    if len(matches) < 1:
        print("\nDevice ID: {}".format(Device_Name))
        print(" IP address: " + device_ip)
        print(" Note: I don't have any sub-interfaces in up up state")
    else:
        for m in matches:
            match_pices = str.split(m)
            # print(match_pices[1])
            sh_ip_arp_output = net_connect.send_command("sh ip arp " + match_pices[0])
            regex = '''(\d+\.\d+\.\d+\.\d+)\s+\d+'''
            pattern = re.compile(regex)
            arp_matches = pattern.findall(sh_ip_arp_output)
            if len(arp_matches) < 1:
                print("\nDevice ID: {}".format(Device_Name))
                print(" IP address: " + device_ip)
                print(" Note: Currently, the network device connected to \"" + match_pices[0] + "\" is down")
            else:
                for m in arp_matches:
                    # print(m)
                    device_para = [{'device_type': device_type, 'ip': m, 'username': username, 'password': password}]
                    connect(device_para)

def find_matches (device_name, cdp_cmd_output, device_ip):
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
            if match not in match_set:
                match_set.add(match)
                # print(match)
                match_lines_list = str.splitlines(match)
                device_ip = re.findall(re.compile('\d+\.\d+\.\d+\.\d+'), match_lines_list[1])
                device_para = [
                    {'device_type': device_type, 'ip': device_ip.pop(), 'username': username, 'password': password}]
                connect(device_para)

if __name__ == '__main__':
    # os.chdir(direc)
    sys.stdout = open('matches_set@' + str(timeStamp) + ".txt", 'w')
    device_para = [{'device_type': device_type, 'ip': ip, 'username': username, 'password': password}]
    connect(device_para)
    for m in sorted(match_set):
        print('\n'+m)
    sys.stdout.close()