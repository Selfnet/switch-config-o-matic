import enum
import config_parsing
from utils import mac_regex, ensure_ztp_mac
from config import db_url, ztp_network, ztp_interface_ip
from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship

Base = declarative_base()
_engine = create_engine(db_url)

def create_scoped_session():
    engine = create_engine(db_url)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

Session = create_scoped_session()

class SwitchStatus(enum.Enum):
    CREATED = 0
    NAMED = 1
    DHCP_SUCCESS = 2
    REBOOTING = 3
    FINISNED = 4
    ERROR = 100

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

class Switch(Base):
    __tablename__ = "switches"

    id = Column(Integer, primary_key=True)
    mac = Column(String, nullable=False)
    name = Column(String)
    status = Column(Enum(SwitchStatus), default=SwitchStatus.CREATED)
    ztp_ip = Column(String)
    final_ip = Column(String)  # The IP of service port 1 which is assigned by the config file

    def __repr__(self):
        return f'<MAC="{self.mac}", NAME="{self.name}", STATUS="{self.status.name}", ' + \
            f'ZTP_IP="{self.ztp_ip}", FINAL_IP="{self.final_ip}">'

class SyslogEntry(Base):
    __tablename__ = "syslog"

    id = Column(Integer, primary_key=True)
    msg = Column(String)
    switch_id = Column(Integer, ForeignKey("switches.id"))

    switch = relationship("Switch", back_populates="syslog_entries")

Switch.syslog_entries = relationship("SyslogEntry", order_by=SyslogEntry.id, back_populates="switch")

def init_db():
    Base.metadata.create_all(_engine)

def get_next_ip():
    with Session() as session:
        used_ips = [sw.ztp_ip for sw in session.query(Switch.ztp_ip).all()]
    used_ips.append(ztp_interface_ip)

    for ip in ztp_network.hosts():
        if not ip.exploded in used_ips:
            return ip.exploded

def add_switch(mac):
    mac = ensure_ztp_mac(mac)
    switch = Switch(mac=mac, ztp_ip=str(get_next_ip()))
    with Session() as session:
        session.add(switch)
        session.commit()

def query_mac(mac):
    mac = ensure_ztp_mac(mac)
    with Session() as session:
        return session.query(Switch).filter(Switch.mac == mac).scalar()

def query_name(name):
    with Session() as session:
        return session.query(Switch).filter(Switch.name == name).first()

def get_macs_names():
    with Session() as session:
        switches = session.query(Switch.mac, Switch.name).all()
    macs = [sw[0] for sw in switches]
    names = [sw[1] for sw in switches if sw[1] is not None]

    return macs, names

def _fill_final_ip(switch):
    ip, _ = config_parsing.get_ip_and_network_port_1(switch.name)
    if ip is None:
        print("Warning: Switch has no IP assigned on port 1.\n" +
              "It will not be possible to check when ZTP is finished.\n" +
              "Please observe this switch manually.")
        return
    switch.final_ip = ip.exploded

def name_switch(mac, name):
    mac = ensure_ztp_mac(mac)
    with Session() as session:
        existing = session.query(Switch).filter(Switch.name == name).all()
        if (len(existing) > 0):
            raise ValueError(f'Name {name} already used by switch {existing[0].mac}')

        sw = session.query(Switch).filter(Switch.mac == mac).one()
        if sw.name is not None:
            print(f'Error: Switch {mac} already named {sw.name}')
            return
        sw.name = name
        sw.status = SwitchStatus.NAMED
        _fill_final_ip(sw)
        session.commit()

def name_last_added_switch(name):
    with Session() as session:
        sw = session.query(Switch).order_by(Switch.id.desc()).first()
    name_switch(sw.mac, name)

def query_all_unfinished_switches():
    with Session() as session:
        return session.query(Switch) \
            .filter(Switch.status != SwitchStatus.FINISNED) \
            .filter(Switch.name is not None) \
            .all()

def get_syslog_entries(mac_or_name):
    with Session() as session:
        if mac_regex.match(mac_or_name):
            mac = ensure_ztp_mac(mac_or_name)
            switch = session.query(Switch).filter(Switch.mac == mac).one()
        else:
            switch = session.query(Switch).filter(Switch.name == mac_or_name).one()

        return [le.msg for le in switch.syslog_entries]

def remove_switch(mac_or_name):
    with Session() as session:
        if mac_regex.match(mac_or_name):
            mac = ensure_ztp_mac(mac_or_name)
            switch = session.query(Switch).filter(Switch.mac == mac).one()
        else:
            switch = session.query(Switch).filter(Switch.name == mac_or_name).one()

        session.delete(switch)
        session.commit()


def set_status(mac_or_name, status: str):
    with Session() as session:
        if mac_regex.match(mac_or_name):
            mac = ensure_ztp_mac(mac_or_name)
            switch = session.query(Switch).filter(Switch.mac == mac).one()
        else:
            switch = session.query(Switch).filter(Switch.name == mac_or_name).one()

        switch.status = SwitchStatus[status.upper()]
        session.commit()
