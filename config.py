import ipaddress

LOG_FORMAT = "%(asctime)s | %(filename)s | %(levelname)s | %(thread)d: %(message)s"

ztp_network = ipaddress.ip_network("192.168.0.0/23")
ztp_interface = "enp0s31f6"
ztp_interface_ip = ztp_network[1].exploded

db_url = "sqlite:///switches.sqlite"

sftp_user = "switch"
sftp_pass = "geheim42"
sftp_ip = ztp_interface_ip
sftp_port = 2222

switch_config_dir = "switch_configs"

dhcp_reload_interval_sec = 10
