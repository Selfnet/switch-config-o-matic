import asyncio
import platform
import subprocess

import config
import db
from db import Switch, SwitchStatus

async def ip_responds_to_ping_async(host):
    ping_process = await asyncio.create_subprocess_exec(
        "ping", "-c", "1", "-I", config.ztp_interface, host)
    return_code = await ping_process.wait()
    return return_code == 0


async def main():
    while True:
        print("Starting")
        with db.Session() as session:
            switches = session.query(Switch) \
                .filter(Switch.status != SwitchStatus.FINISNED) \
                .filter(Switch.name != None) \
                .filter(Switch.final_ip != None) \
                .all()

            ping_tasks = [ip_responds_to_ping_async(sw.final_ip) for sw in switches]
            ping_results = await asyncio.gather(*ping_tasks)

            for ping_successful, switch in zip(ping_results, switches):
                if ping_successful:
                    switch.status = SwitchStatus.FINISNED


if __name__ == "__main__":
    asyncio.run(main())

