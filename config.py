import ipaddress

# You might want to touch these:
ztp_interface = "eth0"
switch_config_dir = "switch_configs"
labelprinter_hostname = "labelprinter-2.workstation.selfnet.de"

# The binary to be executed. Supported values are docker and podman
container_engine = "docker"

# Other options
LOG_FORMAT = "%(asctime)s | %(filename)s | %(levelname)s | %(thread)d: %(message)s"

ztp_network = ipaddress.ip_network("192.168.0.0/23")
ztp_interface_ip = ztp_network[1].exploded

db_url = "sqlite:///switches.sqlite"

sftp_user = "switch"
sftp_pass = "SuperSecretPassword"
sftp_ip = ztp_interface_ip
sftp_port = 2222

dhcp_reload_interval_sec = 10
