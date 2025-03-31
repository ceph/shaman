'''
conftest.py

By default, unit tests run against a SQLite3 database, as that requires no
additional setup. To instead test against a PostgreSQL database, you might:

podman run --rm -d -p 5432:5432 --name shamantest -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=shamantest postgres:16
py.test --db-url postgresql+psycopg2://postgres@localhost:5432/shamantest' ...

Don't forget to remove the container when you are finished:
podman rm -f shamantest
'''
import os
import pytest

from pecan import configuration, conf
from pecan.testing import load_test_app

from shaman import models
from shaman.tests import util

def pytest_addoption(parser):
    parser.addoption(
        '--db-url',
        default='sqlite:///dev.db',
        help='The database to use for testing. For more information see conftest.py'
    )


@pytest.fixture(scope='session')
def db_url(pytestconfig):
    return pytestconfig.getoption('db_url')


class Factory(object):
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


@pytest.fixture
def factory():
    return Factory


@pytest.fixture(autouse=True)
def no_pika_requests(monkeypatch, factory):
    """
    If you don't do anything to patch pika, this fxiture will automatically
    patchn it and prevent outbound requests.
    """
    fake_connection = factory(
        queue_bind=lambda: True,
        close=lambda: True,
        channel=lambda: factory(
            exchange_declare=lambda *a, **kw: True,
            queue_bind=lambda *a: True,
            basic_publish=lambda *a, **kw: True,
            queue_declare=lambda *a, **kw: True,),
    )
    monkeypatch.setattr("pika.BlockingConnection", lambda *a: fake_connection)


def config_file():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, 'config.py')


@pytest.fixture(scope='function')
def config(db_url):
    print(db_url)
    configuration.set_config(dict())
    config_ = configuration.conf_from_file(config_file())
    config_.sqlalchemy_w.url = db_url
    config_.sqlalchemy_ro.url = db_url
    configuration.set_config(
        config_.to_dict(),
        overwrite=True,
     )
    return conf

@pytest.fixture(scope='function')
def app(request, config):
    app = TestApp(load_test_app(config.to_dict()))
    db_engine = conf.sqlalchemy_w.engine
    models.start()
    models.Base.metadata.create_all(db_engine)
    models.Session.commit()
    models.Session.flush()
    models.clear()

    def teardown():
        db_engine = conf.sqlalchemy_w.engine
        models.rollback()
        models.Base.metadata.drop_all(db_engine)

    request.addfinalizer(teardown)
    return app


class TestApp(object):
    """
    A controller test starts a database transaction and creates a fake
    WSGI app.
    """

    __headers__ = {}

    def __init__(self, app):
        self.app = app

    def _do_request(self, url, method='GET', **kwargs):
        methods = {
            'GET': self.app.get,
            'POST': self.app.post,
            'POSTJ': self.app.post_json,
            'PUTJ': self.app.put_json,
            'PUT': self.app.put,
            'HEAD': self.app.head,
            'DELETE': self.app.delete
        }
        kwargs.setdefault('headers', {}).update(self.__headers__)
        return methods.get(method, self.app.get)(str(url), **kwargs)

    def post_json(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a POST request to
        @returns (paste.fixture.TestResponse)
        """
        # support automatic, correct authentication if not specified otherwise
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'POSTJ', **kwargs)

    def post(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a POST request to
        @returns (paste.fixture.TestResponse)
        """
        # support automatic, correct authentication if not specified otherwise
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'POST', **kwargs)

    def get(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a GET request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'GET', **kwargs)

    def put(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a PUT request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'PUT', **kwargs)

    def put_json(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a PUT request to
        @returns (paste.fixture.TestResponse)
        """
        # support automatic, correct authentication if not specified otherwise
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'PUTJ', **kwargs)

    def delete(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a DELETE request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'DELETE', **kwargs)

    def head(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a HEAD request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'HEAD', **kwargs)
