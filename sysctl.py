import subprocess

from config import ztp_interface

original_values = {}

target_values = {
    f"net.ipv6.conf.{ztp_interface}.forwarding": "0",
    "net.ipv6.conf.all.forwarding": "0",
    f"net.ipv6.conf.{ztp_interface}.accept_ra": "0",
    "net.ipv6.conf.all.accept_ra": "0",
}


def _get_value(key):
    return subprocess.check_output(["sysctl", "-n", key]).decode().strip()


def _set_value(key, value):
    subprocess.check_call(["sudo", "sysctl", "-w", f"{key}={value}"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def store_original_values():
    for key in target_values.keys():
        original_values[key] = _get_value(key)


def restore_original_values():
    for key in target_values.keys():
        _set_value(key, original_values[key])


def set_target_values():
    for key, value in target_values.items():
        _set_value(key, value)
