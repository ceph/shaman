from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base


class Node(Base):

    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    host = Column(String(256), nullable=False, unique=True, index=True)
    last_used = Column(DateTime, index=True)
    last_check = Column(DateTime, index=True)

    def __init__(self, host):
        self.host = host

    def __repr__(self):
        try:
            return '<Node %r>' % self.host
        except DetachedInstanceError:
            return '<Node detached>'

    def __json__(self):
        return dict(
            host=self.host,
            last_used=self.last_used,
            last_check=self.last_check,
        )
