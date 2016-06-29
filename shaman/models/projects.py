from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base


class Project(Base):

    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        try:
            return '<Project %r>' % self.name
        except DetachedInstanceError:
            return '<Project detached>'

    def __json__(self):
        return dict(
            name=self.name,
        )


def get_or_create(name, **kw):
    project = Project.filter_by(name=name).first()
    if not project:
        project = Project(name=name)
    return project
