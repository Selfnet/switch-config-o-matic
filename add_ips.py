import os
import glob
import subprocess

from config import switch_config_dir, ztp_interface
from config_parsing import get_ip

cmds = ""

for config_path in glob.glob(f"{switch_config_dir}/*"):
    ip = get_ip(config_path.split("/")[-1])
    if ip is None:
        continue

    cmds += f"addr add {ip} dev {ztp_interface}\n"

subprocess.run(["sudo", "ip", "-batch", "-"], input=cmds.encode(), check=True)

