# Switch-config-o-matic
The purpose of this script is to automate and parallelize setting up Huawei switches.

## Installation and setup
- Clone the repository
- Install the required system packages: dnsmasq, docker
- Install the `python-gobject` system package on Arch-based distros or `python3-gi` on Debian-based distros
- Create a venv that includes system packages (we need `python-gobject`):
  `python -m venv --system-site-packages venv`
- Activate the venv: `. venv/bin/activate`
- Install the other requirements: `pip install -r requirements.txt`
- Download the huawei configs for the switches (eg. trigger a pipeline in https://git.selfnet.de/support/siam/-/tree/generate-all-huawei-configs and download the build_switch_configs artifacts)
- Put them in a folder within this repo (eg. switch_configs)
- Copy masterkey.ini to this folder and insert the actual master key into the file
- Adjust config.py to fit your system (especially `ztp_interface`)
- Start the switch-config-o-matic shell: `python main.py`
- Type `help` to get help on the available commands

## How to start the ZTP process for a switch
- Connect **front-panel port 1** of the target huawei switch to your system
- Type the `add` command in the shell
- Scan the MAC address code on the back of the switch
- Type the `name switch_name` command to name the last added switch "switch_name".
- Type `l` to list the switches with their status
- Type `log switch_name` command to see the (sys)log of the switch "switch_name".
