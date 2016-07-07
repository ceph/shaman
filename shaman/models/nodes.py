import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base


class Node(Base):

    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    host = Column(String(256), nullable=False, unique=True, index=True)
    # we use the old date to push new nodes to the top of the pool
    last_used = Column(DateTime, index=True, default=datetime.datetime(1970, 1, 1))
    last_check = Column(DateTime, index=True)
    healthy = Column(Boolean(), default=True)
    down_count = Column(Integer, default=0)

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
            healthy=self.healthy,
            down_count=self.down_count,
        )
