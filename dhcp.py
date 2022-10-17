import subprocess
import db
import logging
from db import Session, Switch, SwitchStatus
from dhcpconfig import DnsmasqDhcpConfigGenerator


def run_dhcp_config_loop(restart_interval_seconds=5):
    logging.info("Starting DHCP config loop")

    config_gen = DnsmasqDhcpConfigGenerator(
        interface="enp0s20f0u5",
        sftp_user="switch",
        sftp_pass="SuperSecretPassword",
        sftp_ip="192.168.0.1",
        sftp_port=2222
    )

    while True:
        switches = db.query_all_unfinished_switches()
        dnsmasq_config = config_gen.generate_config(switches)
        with open("dnsmasq.conf", "w") as f:
            f.write(dnsmasq_config)

        dnsmasq_result = subprocess.run(["sudo", "timeout", str(restart_interval_seconds),
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


if __name__ == "__main__":
    db.init_db()
    run_dhcp_config_loop()
