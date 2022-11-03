import os
import glob
import subprocess

from config import switch_config_dir, ztp_interface, ztp_network, ztp_interface_ip
from config_parsing import get_ip_and_network_port_1

cmds = f"addr flush dev {ztp_interface}\n"
cmds += f"addr add {ztp_interface_ip}/{ztp_network.prefixlen} dev {ztp_interface}\n"

for config_path in glob.glob(f"{switch_config_dir}/*.cfg"):
    switch_ip, network = get_ip_and_network_port_1(config_path.split("/")[-1].split(".")[0])
    if switch_ip is None or network is None:
        continue

    my_interface_ip = next(network.hosts()).exploded

    cmds += f"addr add {my_interface_ip}/{network.prefixlen} dev {ztp_interface}\n"

subprocess.run(["sudo", "ip", "-batch", "-"], input=cmds.encode(), check=True)
