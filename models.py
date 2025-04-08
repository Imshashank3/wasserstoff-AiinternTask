from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Email(Base):
    __tablename__ = 'emails'
    id = Column(String, primary_key=True)
    sender = Column(String)
    subject = Column(String)
    body = Column(Text)
    timestamp = Column(DateTime)
