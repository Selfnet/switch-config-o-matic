import re
import os
import logging

from config import LOG_FORMAT

mac_regex = re.compile('^(?:[0-9A-Fa-f]{2}[:-]?){5}(?:[0-9A-Fa-f]{2})$')


def configure_logging():
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt='%d.%m.%Y, %H:%M:%S',
        filename="log.txt", filemode='a')

