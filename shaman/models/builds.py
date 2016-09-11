import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref, deferred
from sqlalchemy.event import listen
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base, update_timestamp
from shaman.models.types import JSONType


class Build(Base):

    __tablename__ = 'builds'
    id = Column(Integer, primary_key=True)
    url = Column(String(256))
    log_url = Column(String(256))
    build_id = Column(String(64), index=True)
    ref = Column(String(256), index=True)
    sha1 = Column(String(256), index=True)
    flavor = Column(String(256), nullable=False, index=True, default="default")
    distro = Column(String(256), nullable=False, index=True)
    distro_version = Column(String(256), nullable=False, index=True)
    modified = Column(DateTime, index=True)
    status = Column(String(256), index=True)
    arch = Column(String(256), index=True)
    extra = deferred(Column(JSONType()))

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('builds', lazy='dynamic'))


    allowed_keys = [
        'url',
        'log_url',
        'build_id',
        'ref',
        'sha1',
        'flavor',
        'distro',
        'distro_version',
        'status',
        'arch',
        'extra',
    ]

    def __init__(self, project, **kwargs):
        self.project = project
        self.modified = datetime.datetime.utcnow()
        self.update_from_json(kwargs)

    def __repr__(self):
        try:
            return "<Build {}/{}/{}/{}/{}>".format(
                self.project.name,
                self.ref,
                self.sha1,
                self.distro,
                self.distro_version,
            )
        except DetachedInstanceError:
            return '<Build detached>'

    def __json__(self):
        from shaman.util import parse_distro_release
        codename, version = parse_distro_release(
            self.distro_version,
            self.distro
        )
        return dict(
            url=self.url,
            log_url=self.log_url,
            build_id=self.build_id,
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor,
            distro=self.distro,
            distro_version=version,
            distro_codename=codename,
            status=self.status,
            arch=self.arch,
            extra=self.extra
            modified=self.modified,
            project=self.project.name,
        )


# listen for timestamp modifications
listen(Build, 'before_insert', update_timestamp)
listen(Build, 'before_update', update_timestamp)
