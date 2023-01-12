import os
import cmd
import sys
import subprocess
import logging
import shutil
import glob

import db
import config
import readline
import labelprinter.draw
import labelprinter.printer
from playsound import playsound
from db import create_scoped_session, Switch
from utils import mac_regex, configure_logging
from huawei_syslog import get_human_readable_syslog_messages

Session = create_scoped_session()
configure_logging()

class SwitchConfigurOmaticShell(cmd.Cmd):
    intro = ''
    prompt = 'config-o-matic> '

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.exit_requested = False
        self.histfile = ".cmd_history"

    def do_addonly(self, arg):
        arg = arg.strip()
        if not mac_regex.match(arg):
            print(f'ERROR: Invalid MAC address "{arg}"')
            return

        if db.query_mac(arg):
            print(f'ERROR: MAC address "{arg}" already exists')
            return

        db.add_switch(arg)

        print(f'Added {arg}')

    def do_add(self, _):
        while True:
            mac = input("MAC: ")
            if not mac_regex.match(mac):
                print(f"'{mac}' is not a valid MAC address.")
                playsound("audio/mac_failure.ogg", block=False)
                continue

            try:
                db.add_switch(mac)
                playsound("audio/mac_success.ogg", block=False)
                break
            except Exception as e:
                print(e)
                playsound("audio/mac_failure.ogg", block=False)

        while True:
            name = input("Name: ")
            if len(name) == 0 or len(glob.glob(f"{config.switch_config_dir}/{name}*")) == 0:
                print(f"Switch config for switch '{name}' not found in {config.switch_config_dir}")
                playsound("audio/name_failure.ogg", block=False)
                continue

            try:
                db.name_switch(mac, name)
                playsound("audio/name_success.ogg", block=False)
                break
            except Exception as e:
                print(e)
                playsound("audio/name_failure.ogg")

        print(f'Added {name} ({mac})')

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
        return "Syntax: log [-v] name_or_mac"

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

        try:
            print(f"Printing label for {switch.name}...")
            imgsurf = labelprinter.draw.render_text(switch.name, switch.mac, switch.mac, add_selfnet_s=True)
            labelprinter.printer.print_to_ip(imgsurf, config.labelprinter_hostname)
            print(f"Printed label for {switch.name}.")
        except Exception as e:
            print(f"Printing qr-label failed for {switch.name}: {e}")
            print("Fix the printer, execute the previous name command again and ignore the 'already named' error.")

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

    def preloop(self):
        if os.path.exists(self.histfile):
            readline.read_history_file(self.histfile)

    def postloop(self):
        readline.set_history_length(-1)
        readline.write_history_file(self.histfile)


def main():
    logging.info("     --------------- START switch-config-o-matic ---------------")
    db.init_db()

    sftp_dir = os.path.abspath(config.switch_config_dir)
    if not os.path.exists(sftp_dir):
        os.makedirs(sftp_dir)  # podman does not auto-create volume mounts

    subprocess.call([
        config.container_engine, "run", "--name", "sftp_server", "--rm",
        "-v", f"{os.path.abspath(config.switch_config_dir)}:/home/switch",
        "-p", f"{config.sftp_port}:22",
        "-d", "atmoz/sftp",
        f"{config.sftp_user}:{config.sftp_pass}:{os.getuid()}:{os.getuid()}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.call(["python", "add_ips.py"])

    # Temporarily allow the two python processes to access privileged ports without root,
    # so that we can terminate these processes afterwards
    python_exec = os.path.realpath(shutil.which("python"))
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
    subprocess.call([config.container_engine, "stop", "sftp_server"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
