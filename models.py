from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base

class UserDroit(Base):
    __tablename__ = 'userDroit'
    username = Column(String(200), primary_key=True)
    group = Column(Text)
    level = Column(Integer)
    secret = Column(Text)

    header = ['username', 'group', 'level']
    is_boolean = []
    primary_key = 'username'

    def __init__(self, username=None, group="", level=0):
        self.username = username
        self.group = group
        self.level = level

    def __repr__(self):
        return '<UserDroit %r>' % (self.username)

class Application(Base):
    __tablename__ = 'application'
    id = Column(Integer, primary_key=True)
    nom = Column(String(100))
    key = Column(Text)
    otp_required = Column(Integer)

    header = ['id', 'nom', 'key', 'otp_required']
    is_boolean = ["otp_required"]
    primary_key = 'id'

    def __init__(self, nom=None, key=None):
        self.nom = nom
        self.key = key
        self.otp_required = 0

    def __repr__(self):
        return '<Application %r>' % (self.nom)
