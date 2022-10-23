LOG_FILE = 'syslog_server.log'
# Bei expliziter Addresse des Interfaces muss man immer warten bis der Switch hochgefahren ist...
HOST, PORT = "0.0.0.0", 514

import logging
import utils
import socketserver
from db import create_scoped_session, Switch, SyslogEntry

Session = create_scoped_session()

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        syslog_message = str(bytes.decode(self.request[0].strip()))
        switch_ip = self.client_address[0]

        with Session() as session:
            sw = session.query(Switch).filter(Switch.ztp_ip == switch_ip).one()
            sw.syslog_entries.append(SyslogEntry(msg=syslog_message))
            session.commit()


class SyslogServer():
    def __init__(self):
        self._server = socketserver.UDPServer((HOST, PORT), SyslogUDPHandler)

    def start(self):
        logging.info("Starting syslog server")
        self._server.serve_forever(poll_interval=0.1)

    def stop(self):
        logging.info("Stopping syslog server")
        self._server.shutdown()
        logging.info("Stopped syslog server")


if __name__ == "__main__":
    utils.configure_logging()
    try:
        syslog_server = SyslogServer()
        syslog_server.start()
    except KeyboardInterrupt:
        logging.info("Exit syslog server")
