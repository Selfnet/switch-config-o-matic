import re
import os
import subprocess
from ipaddress import ip_address, ip_network

from config import switch_config_dir


def _rename_config_file_if_necessary(switch_name):
    config_path = f"{switch_config_dir}/{switch_name}"
    if os.path.exists(config_path):
        subprocess.run(["sudo", "mv", config_path, f"{config_path}.cfg"])


def _read_config_lines(switch_name):
    _rename_config_file_if_necessary(switch_name)
    config_path = f"{switch_config_dir}/{switch_name}.cfg"
    with open(config_path, "r") as f:
        config_lines = [l.strip() for l in f.readlines()]
    return config_lines


def get_ip_and_network_port_1(switch_name):
    config_lines = _read_config_lines(switch_name)
    for i in range(len(config_lines)):
        try:
            if config_lines[i] == "interface MultiGE1/0/1" and not config_lines[
                i + 1
            ].startswith("interface"):
                search_area = " ".join(config_lines[i : i + 50])
                match = re.search(
                    r"ip address (?P<ip>\d+.\d+.\d+.\d+) (?P<netmask>\d+.\d+.\d+.\d+)",
                    search_area,
                )
                ip = match.group("ip")
                netmask = match.group("netmask")
                return ip_address(ip), ip_network(f"{ip}/{netmask}", strict=False)
        except:
            continue

    return None, None
