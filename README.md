# Switch-config-o-matic
The purpose of this script is to automate and parallelize setting up Huawei switches.

## Installation and setup
- Clone the repository
- Install the required system packages: dnsmasq, docker/podman (adapt config.container_engine if necessary)
- Create a venv: `python -m venv venv`
- Activate the venv: `. venv/bin/activate`
- Install the other requirements: `pip install -r requirements.txt`
- Download the huawei configs for the switches (eg. trigger a pipeline in https://git.selfnet.de/support/siam/-/tree/generate-all-huawei-configs and download the build_switch_configs artifacts)
- Put them in a folder within this repo (eg. switch_configs)
- Copy masterkey.ini to this folder and insert the actual master key into the file
  > Warning: The masterkey.ini file does not support indentation
- Adjust config.py to fit your system (especially `ztp_interface`)
- Start the switch-config-o-matic shell: `python main.py`
- Type `help` to get help on the available commands

## How to start the ZTP process for a switch
- Connect **front-panel port 1** of the target huawei switch to your system
- Type the `add` command in the shell
- Scan the MAC address code on the back of the switch
- Type the `name switch_name` command to name the last added switch "switch_name".
- Get the printed working-label from the label printer and put it on top of the switch or whereever you like.
- Type `l` to list the switches with their status
- Type `log switch_name` command to see the (sys)log of the switch "switch_name".
- When the process is finished, get the final small label from the label printer and put it on the front panel of the switch (eg. on the very right).

## Statuses the switch can be in
|Name|Meaning|
|----|-------|
|CREATED|The switch was added to the database with its MAC and has to be named next.|
|NAMED|You have said which switch this is. The switch was added to the DHCP server config and we now wait for the switch to request an IP address (this can take up to 15min).|
|DHCP_SUCCESS|The switch has requested an IP address from the DHCP server and is trying to enter the ZTP procedure by getting its config from the SFTP server. If the status is stuck here, please see the log for errors.|
|REBOOTING|The ZTP process was successfull and the switch it reboots itself. The switch will stay in this status until we can ping it at the IP address assigned to port 1 in the config.|
|FINISNED|We can ping the switch. This way we have verified, that the config works correctly. The switch can now be disconnected. A small label with a QR code will be printed now. |

## Download switch configs programmatically

To download all switch configs from the latest GitLab pipeline programmatically, simply run `python3 download_artifacts.py --token YOUR_TOKEN`. The token can be created on GitLab and only requires `read_api` access. Notice that running this script requires the python `requests` module to be installed.
