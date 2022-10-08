import re
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print

mac_regex = re.compile('^(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})$')

if __name__ == "__main__":
    macs = []
    session = PromptSession("config-o-matic> ")

    while True:
        text = session.prompt()
        args = [arg.strip() for arg in text.split()]
        cmd = args[0]

        if cmd in ["exit", "quit", "q"]:
            print('Bye!')
            exit()
        elif cmd == "add":
            arg = args[1]
            if not mac_regex.match(arg):
                print(f'ERROR: Invalid MAC address "{arg}"')
            else:
                print(f'Added {arg}')
                macs.append(arg)
        elif cmd in ["status", "s"]:
            arg = args[1]
            if arg not in macs:
                print(f'ERROR: {arg} does not exist')
            else:
                print(f'Status of {arg}: Example Status')
