import re
import os
import cmd
import sys
import subprocess
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor

import db
import config
import labelprinter.draw
import labelprinter.printer
from dhcp import DhcpServer
from db import create_scoped_session, Switch
from utils import mac_regex, configure_logging
from syslog_server import SyslogServer
from syslog import get_human_readable_syslog_messages

Session = create_scoped_session()
configure_logging()

class SwitchConfigurOmaticShell(cmd.Cmd):
    intro = ''
    prompt = 'config-o-matic> '

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.exit_requested = False

    def do_add(self, arg):
        arg = arg.strip()
        if not mac_regex.match(arg):
            print(f'ERROR: Invalid MAC address "{arg}"')
            return

        if db.query_mac(arg):
            print(f'ERROR: MAC address "{arg}" already exists')
            return

        db.add_switch(arg)

        print(f'Added {arg}')

    def do_status(self, arg):
        arg = arg.strip()

        if arg == "":
            with Session() as session:
                switches = session.query(Switch).all()
            [print(sw) for sw in switches]
            return
        elif mac_regex.match(arg):
            switch = db.query_mac(arg)
        else:
            switch = db.query_name(arg)

        if switch is None:
            print(f'ERROR: A switch with MAC or name "{arg}" does not exist')
            return
        else:
            print(switch)

    def _complete_name_or_mac(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        macs, names = db.get_macs_names()
        identifiers = macs + names
        return [f'{s[offs:]} ' for s in identifiers if s.startswith(mline)]

    def complete_status(self, text, line, begidx, endidx):
        self._complete_name_or_mac(text, line, begidx, endidx)

    def do_list(self, arg=None):
        self.do_status("")

    def do_l(self, arg):
        self.do_list()

    def do_log(self, arg):
        args = arg.split()
        do_verbose = "-v" in args
        while "-v" in args: args.remove("-v")
        name_or_mac = args[0]

        msgs = db.get_syslog_entries(name_or_mac)
        if do_verbose:
            for msg in msgs: print(msg + "\n")
        else:
            readable_msgs = get_human_readable_syslog_messages(msgs)
            for msg in readable_msgs:
                print(msg)

    def help_log(self):
        return "Syntax: syslog [-v] name_or_mac"

    def complete_log(self, text, line, begidx, endidx):
        return self._complete_name_or_mac(text, line, begidx, endidx)

    def do_name(self, arg):
        args = arg.split()
        if len(args) == 1:
            name = args[0]
            db.name_last_added_switch(name)
        elif len(args) == 2:
            name = args[1]
            db.name_switch(args[0], args[1])

        switch = db.query_name(name)

        imgsurf = labelprinter.draw.render_text(switch.name, switch.mac, switch.mac, add_selfnet_s=True)
        labelprinter.printer.print_to_ip(imgsurf, config.labelprinter_hostname)

    def complete_name(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        macs, _ = db.get_macs_names()
        return [f'{s[offs:]} ' for s in macs if s.startswith(mline)]

    def default(self, line):
        line = line.strip()
        if mac_regex.match(line):
            mac = line
            if db.query_mac(mac):
                self.do_status(mac)
            else:
                self.do_add(mac)
        else:
            print(f'ERROR: Unknown syntax: {line}')

    def do_shell(self, arg):
        os.system(arg)

    def do_clear(self, arg=None):
        os.system("clear")

    def do_exit(self, arg=None):
        self.exit_requested = True
        db.Session.remove()
        return True

    def do_quit(self, arg):
        return self.do_exit()

    def do_q(self, arg):
        return self.do_exit()

    def emptyline(self):
        pass

    def get_valid_commands(self):
        names = self.get_names()
        valid = [name[4:] for name in names if name[:3] == 'do_']
        return valid

    def cmdloop_with_keyboard_interrupt(self):
        while not self.exit_requested:
            try:
                self.cmdloop()
                self.exit_requested = True
            except KeyboardInterrupt:
                sys.stdout.write('\n')
            except Exception as e:
                print(e)


def main():
    logging.info("     --------------- START switch-config-o-matic ---------------")
    db.init_db()

    python_exec = os.path.realpath(shutil.which("python"))
    print(python_exec)

    subprocess.call(["python", "add_ips.py"])

    # Temporarily allow the two python processes to access privileged ports without root,
    # so that we can terminate these processes afterwards
    subprocess.call(["sudo", "setcap", "cap_net_bind_service=+ep", python_exec])

    syslog_process = subprocess.Popen(["python", "syslog_server.py"])
    dhcp_process = subprocess.Popen(["python", "dhcp.py"])
    ping_process = subprocess.Popen(["python", "check_finished.py"])

    # Remove privileged ports exception
    subprocess.call(["sudo", "setcap", "-r", python_exec])

    print('Welcome to the switch-config-o-matic shell.   Type help or ? to list commands.\n')
    SwitchConfigurOmaticShell().cmdloop_with_keyboard_interrupt()
    syslog_process.terminate()
    dhcp_process.terminate()
    ping_process.terminate()


if __name__ == "__main__":
    main()

