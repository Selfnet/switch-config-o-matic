import subprocess
import db
import logging
import utils

import dhcpconfig
from config import dhcp_reload_interval_sec
from db import create_scoped_session, Switch, SwitchStatus

Session = create_scoped_session()

class DhcpServer():
    def __init__(self):
        self.shutdown_requested = False

    def start(self):
        logging.info("Starting DHCP config loop")
        self.shutdown_requested = False

        while not self.shutdown_requested:
            switches = db.query_all_unfinished_switches()
            dnsmasq_config = dhcpconfig.generate_config(switches)
            with open("dnsmasq.conf", "w") as f:
                f.write(dnsmasq_config)

            dnsmasq_result = subprocess.run(["sudo", "timeout", str(dhcp_reload_interval_sec),
                "dnsmasq", "--no-daemon", "--conf-file=dnsmasq.conf"], text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            output = dnsmasq_result.stdout
            lines = output.splitlines()
            ack_lines = [l for l in lines if "DHCPACK" in l]

            for line in ack_lines:
                mac = line.split()[3].lower()
                with Session() as session:
                    sw = session.query(Switch).filter(Switch.mac == mac).one()
                    if sw.status < SwitchStatus.DHCP_SUCCESS:
                        sw.status = SwitchStatus.DHCP_SUCCESS
                    session.commit()

            if len(lines) > 0:
                with open("dnsmasq.log", "a") as logfile:
                    logfile.write("\n".join(lines) + "\n\n")

        logging.info("Stopped DHCP config loop")

    def stop(self):
        self.shutdown_requested = True


if __name__ == "__main__":
    db.init_db()
    utils.configure_logging()
    server = DhcpServer()
    server.start()
