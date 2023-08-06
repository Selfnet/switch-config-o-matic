import asyncio
import datetime
import time

import config
import db
import labelprinter.draw
import labelprinter.printer
from db import Switch, SwitchStatus


async def ip_responds_to_ping_async(host):
    ping_process = await asyncio.create_subprocess_exec(
        "ping",
        "-c",
        "1",
        "-I",
        config.ztp_interface,
        host,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return_code = await ping_process.wait()
    return return_code == 0


async def main():
    while True:
        with db.Session() as session:
            # Check for successful config retrieval
            switches = (
                session.query(Switch)
                .filter(Switch.status == SwitchStatus.DHCP_SUCCESS)
                .all()
            )

            download_success = "Download file successfully."
            rebooting = "After 0 seconds activation will be performed."

            for sw in switches:
                if any(download_success in le.msg for le in sw.syslog_entries) and any(
                    rebooting in le.msg for le in sw.syslog_entries
                ):
                    sw.status = SwitchStatus.REBOOTING
                    session.commit()

            switches = (
                session.query(Switch)
                .filter(Switch.status != SwitchStatus.FINISHED)
                .filter(Switch.name != None)
                .filter(Switch.final_ip != None)
                .all()
            )

            ping_tasks = [ip_responds_to_ping_async(sw.final_ip) for sw in switches]
            ping_results = await asyncio.gather(*ping_tasks)

            for ping_successful, switch in zip(ping_results, switches):
                if ping_successful:
                    try:
                        if config.use_labelprinter:
                            print(f"Printing qr-label for {switch.name}...")
                            imgsurf = labelprinter.draw.render_small_label(switch.name)
                            labelprinter.printer.print_to_ip(
                                imgsurf, config.labelprinter_hostname
                            )
                    except Exception as e:
                        print(
                            f"Printing qr-label failed for {switch.name}: {e}. Please fix the printer."
                        )
                        continue
                    finally:
                        switch.status = SwitchStatus.FINISHED
                        switch.finished_date = datetime.datetime.now()
                        session.commit()

            time.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
