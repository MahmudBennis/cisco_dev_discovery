
import paramiko
import netmiko
from netmiko import ConnectHandler

class CiscoConnect:
    device_para = {}
    device_name = ''
    device_ip = ''
    dev_connect = None

    def __init__(self, device_type, ip, username, password):
        self.device_para = {'device_type': device_type, 'ip': ip, 'username': username, 'password': password}
        self.device_ip = ip

    def connect (self):
        device_para = self.device_para
        try:
            self.dev_connect = ConnectHandler(**device_para)
            self.device_name = self.dev_connect.find_prompt()
        except paramiko.ssh_exception.AuthenticationException:
            print("\nDevice ID: \"I\'ve got an Authentication error\"")
            print(" IP address: {}".format(self.device_ip))
            pass
        except netmiko.ssh_exception.NetMikoTimeoutException:
            print("\nDevice ID: \"This Device is UnReachable\"")
            print(" IP address: {}".format(self.device_ip))
            pass
        except Exception as e:
            print("\nDevice ID: \"There was an Error\"")
            print(" IP address: {}".format(self.device_ip))
            print(' Error Message: \"' + str(e) + '\"')
            pass
        return self.dev_connect

    def send_cmnd(self, cmd):
        output = self.dev_connect.send_command(cmd)
        return output

    def disconnect(self):
       return self.dev_connect.disconnect()
