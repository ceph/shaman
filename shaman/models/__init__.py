import datetime
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import scoped_session, sessionmaker, object_session, mapper
from sqlalchemy.ext.declarative import declarative_base
from pecan import conf


class _EntityBase(object):
    """
    A custom declarative base that provides some Elixir-inspired shortcuts.
    """

    allowed_keys = []

    @classmethod
    def filter_by(cls, *args, **kwargs):
        return cls.query.filter_by(*args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.query.get(*args, **kwargs)

    def flush(self, *args, **kwargs):
        object_session(self).flush([self], *args, **kwargs)

    def delete(self, *args, **kwargs):
        object_session(self).delete(self, *args, **kwargs)

    def as_dict(self):
        return dict((k, v) for k, v in self.__dict__.items()
                    if not k.startswith('_'))

    def update_from_json(self, data):
        """
        We received a JSON blob with updated metadata information
        that needs to update some fields
        """
        for key in self.allowed_keys:
            for key in data.keys():
                setattr(self, key, data[key])


Session = scoped_session(sessionmaker())
metadata = MetaData()
Base = declarative_base(cls=_EntityBase)
Base.query = Session.query_property()


# Listeners:

@event.listens_for(mapper, 'init')
def auto_add(target, args, kwargs):
    Session.add(target)


def update_timestamp(mapper, connection, target):
    """
    Automate the 'modified' attribute when a model changes
    """
    target.modified = datetime.datetime.utcnow()


# Utilities:

def get_or_create(model, **kwargs):
    instance = model.filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        commit()
        return instance


def init_model():
    """
    This is a stub method which is called at application startup time.

    If you need to bind to a parse database configuration, set up tables or
    ORM classes, or perform any database initialization, this is the
    recommended place to do it.

    For more information working with databases, and some common recipes,
    see http://pecan.readthedocs.org/en/latest/databases.html

    For creating all metadata you would use::

        Base.metadata.create_all(conf.sqlalchemy.engine)

    """
    conf.sqlalchemy_w.engine = _engine_from_config(conf.sqlalchemy_w)
    conf.sqlalchemy_ro.engine = _engine_from_config(conf.sqlalchemy_ro)


def _engine_from_config(configuration):
    configuration = dict(configuration)
    url = configuration.pop('url')
    return create_engine(url, **configuration)


def start():
    Session.bind = conf.sqlalchemy_w.engine
    metadata.bind = conf.sqlalchemy_w.engine


def start_read_only():
    Session.bind = conf.sqlalchemy_ro.engine
    metadata.bind = conf.sqlalchemy_ro.engine


def commit():
    Session.commit()


def rollback():
    Session.rollback()


def clear():
    Session.close()


def flush():
    Session.flush()


from projects import Project  # noqa
from repos import Repo  # noqa
from nodes import Node  # noqa
from archs import Arch  # noqa
from builds import Build  # noqa
