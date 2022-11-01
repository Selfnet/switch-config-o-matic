import re
import os
import logging
from lxml import etree

from config import LOG_FORMAT

mac_regex = re.compile('^(?:[0-9A-Fa-f]{2}[:-]?){5}(?:[0-9A-Fa-f]{2})$')


def configure_logging():
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt='%d.%m.%Y, %H:%M:%S',
        filename="log.txt", filemode='a')


def ensure_ztp_mac(mac):
    if not ":" in mac:
        mac = ":".join(re.findall("..", mac))

    # The code contains the management interface's MAC which ends on a zero
    # The ZTP MAC ends on a one. Set that here:
    mac = mac[:-1] + "3"
    mac = mac.lower()

    return mac


def xml_to_keyvalue(xml):
    result = ""
    root = etree.fromstring(xml)
    result = ", ".join([f"{node.tag}={node.text}" for node in root.iter("*") if len(node) == 0])

    return result
