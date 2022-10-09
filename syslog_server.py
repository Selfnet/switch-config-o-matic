LOG_FILE = 'youlogfile.log'
# Bei expliziter Addresse des Interfaces muss man immer warten bis der Switch hochgefahren ist...
HOST, PORT = "0.0.0.0", 514

import logging
import socketserver
import db
from db import Switch, SyslogEntry

logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='', filename=LOG_FILE, filemode='a')

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        syslog_message = str(bytes.decode(self.request[0].strip()))
        switch_ip = self.client_address[0]
        print(f"{switch_ip}: {syslog_message}")

        with db.Session() as session:
            sw = session.query(Switch).filter(Switch.ip == switch_ip).one()
            sw.syslog_entries.append(SyslogEntry(msg=syslog_message))
            session.commit()

        logging.info(syslog_message)

if __name__ == "__main__":
    try:
        server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.1)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")
