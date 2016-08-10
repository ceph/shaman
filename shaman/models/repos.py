import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listen
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base, update_timestamp


class Repo(Base):

    __tablename__ = 'repos'
    id = Column(Integer, primary_key=True)
    url = Column(String(256))
    chacra_url = Column(String(256))
    ref = Column(String(256), index=True)
    sha1 = Column(String(256), index=True)
    flavor = Column(String(256), nullable=False, index=True, default="default")
    distro = Column(String(256), nullable=False, index=True)
    distro_version = Column(String(256), nullable=False, index=True)
    modified = Column(DateTime, index=True)
    status = Column(String(256), index=True)

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('repos', lazy='dynamic'))

    allowed_keys = [
        'url',
        'chacra_url',
        'ref',
        'sha1',
        'distro',
        'distro_version',
        'status',
        'flavor',
    ]

    def __init__(self, project, **kwargs):
        self.project = project
        self.modified = datetime.datetime.utcnow()
        self.update_from_json(kwargs)

    def __repr__(self):
        try:
            return "<Repo {}/{}/{}/{}/{}>".format(
                self.project.name,
                self.ref,
                self.sha1,
                self.distro,
                self.distro_version,
            )
        except DetachedInstanceError:
            return '<Repo detached>'

    def __json__(self):
        return dict(
            url=self.url,
            chacra_url=self.chacra_url,
            ref=self.ref,
            sha1=self.sha1,
            distro=self.distro,
            distro_version=self.distro_version,
            modified=self.modified,
            status=self.status,
        )


# listen for timestamp modifications
listen(Repo, 'before_insert', update_timestamp)
listen(Repo, 'before_update', update_timestamp)
