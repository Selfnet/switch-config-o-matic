import enum
from utils import mac_regex
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
    FINISNED = 3
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
    ip = Column(String)

    def __repr__(self):
        return f'MAC="{self.mac}", NAME="{self.name}", STATUS="{self.status.name}", IP="{self.ip}"'

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
        used_ips = [sw.ip for sw in session.query(Switch.ip).all()]
    used_ips.append(ztp_interface_ip)

    return next(ip for ip in ztp_network.hosts() if not ip in used_ips)

def add_switch(mac):
    switch = Switch(mac=mac, ip=get_next_ip())
    with Session() as session:
        session.add(switch)
        session.commit()

def query_mac(mac):
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

def name_last_added_switch(name):
    with Session() as session:
        sw = session.query(Switch).order_by(Switch.id.desc()).first()
        sw.name = name
        sw.status = SwitchStatus.NAMED
        session.commit()

def name_switch(mac, name):
    with Session() as session:
        sw = session.query(Switch).filter(Switch.mac == mac).one()
        if sw.name != None:
            raise ValueError(f'Switch {mac} already named {sw.name}')
        sw.name = name
        sw.status = SwitchStatus.NAMED
        session.commit()

def query_all_unfinished_switches():
    with Session() as session:
        return session.query(Switch) \
            .filter(Switch.status != SwitchStatus.FINISNED) \
            .filter(Switch.name != None)

def get_syslog_entries(mac_or_name):
    with Session() as session:
        if mac_regex.match(mac_or_name):
            switch = session.query(Switch).filter(Switch.mac == mac_or_name).one()
        else:
            switch = session.query(Switch).filter(Switch.name == mac_or_name).one()

        return [le.msg for le in switch.syslog_entries]
