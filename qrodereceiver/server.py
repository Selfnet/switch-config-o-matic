# This script simulates a wireless qr code scanner with a smartphone
# It hosts a simple Flask server
# which types received qr code contents with the keyboard.
# To be used in conjunction with the android app "BinaryEye":
# https://github.com/markusfisch/BinaryEye
# You can configure the server address in the app settings.

import re
from flask import Flask, request
from pynput.keyboard import Controller

keyboard = Controller()

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

mac_regex = re.compile('^(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})$')

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    qr = request.args.to_dict()["content"]

    if mac_regex.match(qr):
        qr += "\n"
    else:
        qr += " "

    keyboard.type(qr)
    
    print(qr)
    return ""

app.run(host="0.0.0.0", debug=False)
