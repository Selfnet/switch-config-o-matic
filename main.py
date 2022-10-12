import re
import os
import cmd
import sys

import db
from db import Session, Switch
from utils import mac_regex

class SwitchConfigurOmaticShell(cmd.Cmd):
    intro = 'Welcome to the switch-config-o-matic shell.   Type help or ? to list commands.\n'
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
    
    def _complete_name_or_mac(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        macs, names = db.get_macs_names()
        identifiers = macs + names
        return [f'{s[offs:]} ' for s in identifiers if s.startswith(mline)]
    
    def _get_time_from_syslog_msg(self, msg):
        time_contained = msg.split(";")[0]
        time_ = re.match(r"<.*>(.*) HUAWEI", time_contained, re.DOTALL).groups()[0]
        return time_

    def complete_status(self, text, line, begidx, endidx):
        self._complete_name_or_mac(text, line, begidx, endidx)

    def do_list(self, arg=None):
        self.do_status("")

    def do_l(self, arg):
        self.do_list()
    
    def do_syslog(self, arg):
        args = arg.split()
        do_verbose = "-v" in args
        while "-v" in args: args.remove("-v")
        name_or_mac = args[0]

        msgs = db.get_syslog_entries(name_or_mac)
        if do_verbose:
            for msg in msgs: print(msg + "\n")
        else:
            try:
                for msg in msgs:
                    if not "OPS_LOG_USERDEFINED_INFORMATION" in msg:
                        continue
                    time_ = self._get_time_from_syslog_msg(msg)
                    msg_text = msg.split("; ")[1].split("(")[0]
                    print(f"{time_} | {msg_text}")
            except:
                print(msg)
    
    def help_syslog(self):
        return "Syntax: syslog [-v] name_or_mac"
    
    def complete_syslog(self, text, line, begidx, endidx):
        return self._complete_name_or_mac(text, line, begidx, endidx)

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

    def do_errors(self, arg):
        for msg in db.get_syslog_entries(arg):
            try:
                self._get_time_from_syslog_msg
                body = msg.split(";")[1]
                if "<error>" in body:
                    tags = re.findall(r"<error-tag>(.*)</error-tag>", body)
                    error_msgs = re.findall(r"<error-message.*>(.*)</error-message>", body)
                    
                    for error in zip(tags, error_msgs):
                        print(f"{time_} | {error[0]} | {error[1]}")
            except:
                print(msg)
    
    def complete_errors(self, text, line, begidx, endidx):
        return self._complete_name_or_mac(text, line, begidx, endidx)

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
    
    def cmdloop_with_keyboard_interrupt(self):
        doQuit = False
        while doQuit != True:
            try:
                self.cmdloop()
                doQuit = True
            except KeyboardInterrupt:
                sys.stdout.write('\n')


if __name__ == "__main__":
    db.init_db()
    SwitchConfigurOmaticShell().cmdloop_with_keyboard_interrupt()
