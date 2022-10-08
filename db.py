import enum
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)

class SwitchStatus(enum.Enum):
    CREATED = 0
    NAMED = 1
    DHCP_SUCCESSED = 2
    FINISNED = 3
    ERROR = 100


class Switch(Base):
    __tablename__ = "switches"

    id = Column(Integer, primary_key=True)
    mac = Column(String, nullable=False)
    name = Column(String)
    status = Column(Enum(SwitchStatus), default=SwitchStatus.CREATED)
    ip = Column(String)

    def __repr__(self):
        return f'MAC="{self.mac}", NAME="{self.name}", STATUS="{self.status.name}", IP="{self.ip}"'


def init_db():
    Base.metadata.create_all(engine)

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
        session.commit()

def name_switch(mac, name):
    with Session() as session:
        sw = session.query(Switch).filter(Switch.mac == mac).one()
        sw.name = name
        session.commit() 
