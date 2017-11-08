from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base

class UserDroit(Base):
	__tablename__ = 'userDroit'
	username = Column(String(200), primary_key=True)
	group = Column(Text)
	level = Column(Integer)

	header = ['username', 'group', 'level']
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

	header = ['id', 'nom', 'key']
	primary_key = 'id'
	
	def __init__(self, nom=None, key=None):
		self.nom = nom
		self.key = key
		
	def __repr__(self):
		return '<Application %r>' % (self.nom)