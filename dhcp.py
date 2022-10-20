import subprocess
import db
import logging
import utils
from db import create_scoped_session, Switch, SwitchStatus
from dhcpconfig import DnsmasqDhcpConfigGenerator

Session = create_scoped_session()

class DhcpServer():
    def __init__(self, restart_interval_seconds=5):
        self.shutdown_requested = False
        self.restart_interval_seconds = restart_interval_seconds
        self.config_gen = DnsmasqDhcpConfigGenerator(
            interface="enp0s31f6",
            sftp_user="switch",
            sftp_pass="geheim42",
            sftp_ip="192.168.0.1",
            sftp_port=2222
        )

    def start(self):
        logging.info("Starting DHCP config loop")
        self.shutdown_requested = False

        while not self.shutdown_requested:
            switches = db.query_all_unfinished_switches()
            dnsmasq_config = self.config_gen.generate_config(switches)
            with open("dnsmasq.conf", "w") as f:
                f.write(dnsmasq_config)

            dnsmasq_result = subprocess.run(["sudo", "timeout", str(self.restart_interval_seconds),
                "dnsmasq", "--no-daemon", "--conf-file=dnsmasq.conf"], text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            output = dnsmasq_result.stdout
            lines = output.splitlines()
            ack_lines = [l for l in lines if "DHCPACK" in l]

            for line in ack_lines:
                mac = line.split()[3]
                with Session() as session:
                    sw = session.query(Switch).filter(Switch.mac == mac).one()
                    if sw.status < SwitchStatus.DHCP_SUCCESS:
                        sw.status = SwitchStatus.DHCP_SUCCESS
                    session.commit()

            if len(ack_lines) > 0:
                logging.debug(ack_lines)

        logging.info("Stopped DHCP config loop")

    def stop(self):
        self.shutdown_requested = True


if __name__ == "__main__":
    db.init_db()
    utils.configure_logging()
    server = DhcpServer(10)
    server.start()
