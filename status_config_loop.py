import db
import asyncio
from db import Session, Switch, SwitchStatus
from dhcpconfig import DnsmasqDhcpConfigGenerator

async def main():
    #db.add_switch("b0:22:7a:e6:91:34")
    #db.name_last_added_switch("ar3-26a-2")

    config_gen = DnsmasqDhcpConfigGenerator(
        interface="enp0s20f0u5",
        sftp_user="switch",
        sftp_pass="geheim42",
        sftp_ip="192.168.0.1"
    )

    dnsmasq_process = None

    while True:
        switches = db.query_all_unfinished_switches()
        dnsmasq_config = config_gen.generate_config(switches)
        with open("dnsmasq.conf", "w") as f:
            f.write(dnsmasq_config)
        
        if dnsmasq_process is not None:
            await (await asyncio.create_subprocess_exec("sudo", "killall", "dnsmasq")).wait()
            await dnsmasq_process.wait()
            output = (await dnsmasq_process.stderr.read(1024)).decode("utf-8")
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
                print(ack_lines)
        
        dnsmasq_process = await asyncio.create_subprocess_exec(
            "sudo", "dnsmasq", "--no-daemon", "--conf-file=dnsmasq.conf",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        await asyncio.sleep(5)


if __name__ == "__main__":
    db.init_db()
    asyncio.run(main())
