class DnsmasqDhcpConfigGenerator():
    def __init__(self, interface, sftp_user, sftp_pass, sftp_ip):
        self.interface = interface
        self.sftp_user = sftp_user
        self.sftp_pass = sftp_pass
        self.sftp_ip = sftp_ip

    def generate_config(self, switches):
        config_lines = [
            "port=0",  # Disable DNS server
            f"interface={self.interface}",
            "dhcp-option=3,0.0.0.0",  # No gateway / router
            "dhcp-ignore=tag:!known"  # Ignore all devices not specified below using dhcp-host
        ]

        for sw in switches:
            # Example: sftp://switch:geheim42@192.168.0.1/ar-26a-2.cfg
            sftp_path = f"sftp://{self.sftp_user}:{self.sftp_pass}@{self.sftp_ip}/{sw['name']}.cfg"

            config_lines.append(f"\n######### Switch: {sw['name']} ({sw['mac']}) #########")
            # Give this switch its specified IP-address
            config_lines.append(f"dhcp-host={sw['mac']},{sw['ip']}")
            # Creates a named "MAC adress filter"
            config_lines.append(f"dhcp-host={sw['mac']},set:{sw['name']}")
            # Only send the DHCP option to this specific device
            config_lines.append(f"dhcp-option=set:{sw['name']},67,{sftp_path}")
        
        config_lines.append("")  # Newline at the end of the config file
        return "\n".join(config_lines)


if __name__ == "__main__":
    confgen = DnsmasqDhcpConfigGenerator(interface="enp0s31f6", sftp_user="switch",
        sftp_pass="geheim42", sftp_ip="192.168.0.1")
    
    switches = [
        {
            "mac": "b0:22:7a:e6:91:34",
            "name": "ar-26a-2",
            "ip": "192.168.0.10"
        },
        {
            "mac": "00:00:00:00:00:00",
            "name": "testswitch",
            "ip": "192.168.0.222"
        },
    ]

    print(confgen.generate_config(switches))
