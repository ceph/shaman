import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listen
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base, update_timestamp


class Repo(Base):

    __tablename__ = 'repos'
    id = Column(Integer, primary_key=True)
    url = Column(String(256))
    ref = Column(String(256), index=True)
    sha1 = Column(String(256), index=True)
    distro = Column(String(256), nullable=False, index=True)
    distro_version = Column(String(256), nullable=False, index=True)
    modified = Column(DateTime, index=True)
    signed = Column(Boolean(), default=False)
    type = Column(String(12))
    status = Column(String(256), index=True)

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('repos', lazy='dynamic'))

    def __init__(self, project, ref, sha1, distro, distro_version):
        self.project = project
        self.ref = ref
        self.sha1 = sha1
        self.distro = distro
        self.distro_version = distro_version
        self.modified = datetime.datetime.utcnow()

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
            ref=self.ref,
            sha1=self.sha1,
            distro=self.distro,
            distro_version=self.distro_version,
            modified=self.modified,
            signed=self.signed,
            type=self.type,
            status=self.status,
        )

    @property
    def metric_name(self):
        return "repos.%s.%s.%s.%s" % (
            self.project.name,
            self.ref,
            self.distro,
            self.distro_version,
        )


# listen for timestamp modifications
listen(Repo, 'before_insert', update_timestamp)
listen(Repo, 'before_update', update_timestamp)
