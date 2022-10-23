import re

from config import switch_config_dir

def _read_config_lines(switch_name):
    config_path = f"{switch_config_dir}/{switch_name}"
    with open(config_path, "r") as f:
        config_lines = [l.strip() for l in f.readlines()]
    return config_lines

def get_ip(switch_name):
    config_lines = _read_config_lines(switch_name)
    for i in range(len(config_lines)):
        if config_lines[i] == "interface MultiGE1/0/1" and not config_lines[i+1].startswith("interface"):
            search_area = " ".join(config_lines[i:i+50])
            ip = re.search(r"ip address (?P<ip>\d+.\d+.\d+.\d+)", search_area).group("ip")
            return ip