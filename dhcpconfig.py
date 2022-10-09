class DnsmasqDhcpConfigGenerator():
    def __init__(self, interface, sftp_user, sftp_pass, sftp_ip, sftp_port):
        self.interface = interface
        self.sftp_user = sftp_user
        self.sftp_pass = sftp_pass
        self.sftp_ip = sftp_ip
        self.sftp_port = sftp_port

    def generate_config(self, switches):
        config_lines = [
            "port=0",  # Disable DNS server
            f"interface={self.interface}",
            "dhcp-option=3,0.0.0.0",  # No gateway / router
            "dhcp-ignore=tag:!known",  # Ignore all devices not specified below using dhcp-host
            "dhcp-range=192.168.0.5,192.168.0.250,2m"
        ]

        for sw in switches:
            # Example: sftp://switch:geheim42@192.168.0.1/ar-26a-2.cfg
            sftp_path = f"sftp://{self.sftp_user}:{self.sftp_pass}@{self.sftp_ip}:{self.sftp_port}/{sw.name}.cfg"

            config_lines.append(f"\n######### Switch: {sw.name} ({sw.mac}) #########")
            # Give this switch its specified IP-address and creates a named "MAC adress filter"
            config_lines.append(f"dhcp-host={sw.mac},{sw.ip},set:{sw.name}")
            # Only send the DHCP option to this specific device
            config_lines.append(f"dhcp-option=set:{sw.name},67,{sftp_path}")
            # Specify our IP address as syslog server
            config_lines.append(f"dhcp-option=set:{sw.name},7,192.168.0.1")
        
        config_lines.append("")
        return "\n".join(config_lines)
