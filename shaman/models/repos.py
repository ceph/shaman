import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref, deferred
from sqlalchemy.event import listen
from sqlalchemy.orm.exc import DetachedInstanceError
from shaman.models import Base, update_timestamp
from shaman.models.types import JSONType


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
    modified = Column(DateTime(timezone=True), index=True)
    status = Column(String(256), index=True)
    extra = deferred(Column(JSONType()))

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('repos', lazy='dynamic'))

    archs = relationship("Arch", cascade="all, delete")

    allowed_keys = [
        'url',
        'chacra_url',
        'ref',
        'sha1',
        'distro',
        'distro_version',
        'status',
        'flavor',
        'extra',
    ]

    def __init__(self, project, **kwargs):
        self.project = project
        self.modified = datetime.datetime.now(datetime.timezone.utc)
        self.update_from_json(kwargs)

    @property
    def arch(self):
        return ", ".join([arch.name for arch in self.archs])

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
        from shaman.util import parse_distro_release
        codename, version = parse_distro_release(
            self.distro_version,
            self.distro
        )
        return dict(
            url=self.url,
            chacra_url=self.chacra_url,
            ref=self.ref,
            sha1=self.sha1,
            distro=self.distro,
            distro_version=version,
            distro_codename=codename,
            modified=self.modified,
            status=self.status,
            flavor=self.flavor,
            project=self.project.name,
            archs=[arch.name for arch in self.archs],
            extra=self.extra
        )

    def get_url(self):
        """
        This model object is mainly consumed by the UI. Since the template will
        not always have a full concept of what a url part means, this helper
        method will construct what the (full) relative URL to this object is.
        """
        url = "/repos/{project}/{ref}/{sha1}/{flavor}/{_id}/"
        return url.format(
            project=self.project.name,
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor or 'default',
            _id=self.id
        )


# listen for timestamp modifications
listen(Repo, 'before_insert', update_timestamp)
listen(Repo, 'before_update', update_timestamp)
