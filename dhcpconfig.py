from config import *


def generate_config(switches):
    masterkey_file = "/masterkey.ini"
    patch_file = "/patchfile.PAT"

    config_lines = [
        "port=0",  # Disable DNS server
        f"interface={ztp_interface}",
        "dhcp-option=3,0.0.0.0",  # No gateway / router
        "dhcp-ignore=tag:!known",  # Ignore all devices not specified below using dhcp-host
        f"dhcp-range={ztp_network[2]},{ztp_network[-2]},30m",
    ]

    for sw in switches:
        # Example: sftp://switch:SuperSecretPassword@192.168.0.1/ar-26a-2.cfg
        sftp_path = (
            f"sftp://{sftp_user}:{sftp_pass}@{sftp_ip}:{sftp_port}/{sw.name}.cfg"
        )

        config_lines.append(f"\n######### Switch: {sw.name} ({sw.mac}) #########")
        # Give this switch its specified IP-address and creates a named "MAC adress filter"
        config_lines.append(f"dhcp-host={sw.mac},{sw.ztp_ip},set:{sw.name}")
        # Only send the DHCP option to this specific device
        config_lines.append(f"dhcp-option=set:{sw.name},67,{sftp_path}")
        # Specify our IP address as syslog server
        config_lines.append(f"dhcp-option=set:{sw.name},7,{ztp_interface_ip}")
        # Set intermediate file option to set the master key
        config_lines.append(
            f"dhcp-option=set:{sw.name},145,masterfile={masterkey_file};patchfile={patch_file}"
        )

    config_lines.append("")
    return "\n".join(config_lines)
