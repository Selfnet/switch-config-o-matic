import cmd
import re
import os

import db
from db import Session, Switch, SwitchStatus

mac_regex = re.compile('^(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})$')

class SwitchConfigurOmaticShell(cmd.Cmd):
    intro = 'Welcome to the Switch-config-o-matic shell.   Type help or ? to list commands.\n'
    prompt = 'config-o-matic> '

    def __init__(self):
        cmd.Cmd.__init__(self)

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

    def complete_status(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        macs, names = db.get_macs_names()
        identifiers = macs + names
        return [f'{s[offs:]} ' for s in identifiers if s.startswith(mline)]

    def do_list(self, arg=None):
        self.do_status("")

    def do_l(self, arg):
        self.do_list()
    
    def do_syslog(self, arg):
        with Session() as session:
            if mac_regex.match(arg):
                switch = session.query(Switch).filter(Switch.mac == arg).one()
            else:
                switch = session.query(Switch).filter(Switch.name == arg).one()

            for logentry in switch.syslog_entries:
                print(logentry.msg)
    
    def complete_syslog(self, text, line, begidx, endidx):
        return self.complete_status(text, line, begidx, endidx)

    def do_name(self, arg):
        args = arg.split()
        if len(args) == 1:
            db.name_last_added_switch(args[0])
        elif len(args) == 2:
            db.name_switch(args[0], args[1])
    
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
        exit()

    def do_quit(self, arg):
        self.do_exit()

    def do_q(self, arg):
        self.do_exit()

    def emptyline(self):
        pass


if __name__ == "__main__":
    db.init_db()
    SwitchConfigurOmaticShell().cmdloop()
