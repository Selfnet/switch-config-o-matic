import re
import glob
import subprocess

from config import switch_config_dir, ztp_interface

def get_ip(config_lines):
    for i in range(len(config_lines)):
        if config_lines[i] == "interface MultiGE1/0/1" and not config_lines[i+1].startswith("interface"):
            search_area = " ".join(config_lines[i:i+50])
            ip = re.search(r"ip address (?P<ip>\d+.\d+.\d+.\d+)", search_area).group("ip")
            return ip

cmds = ""

for config_path in glob.glob(f"{switch_config_dir}/*"):
    with open(config_path, "r") as f:
        config_lines = [l.strip() for l in f.readlines()]
    ip = get_ip(config_lines)
    if ip is None:
        continue

    cmds += f"addr add {ip} dev {ztp_interface}\n"


subprocess.run(["sudo", "ip", "-batch", "-"], input=cmds.encode(), check=True)

