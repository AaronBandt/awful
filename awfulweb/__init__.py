from pyramid.config import Configurator
from .views import local_groupfinder
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow, Authenticated
from pyramid.renderers import JSON
import logging
import ConfigParser
from sqlalchemy import engine_from_config
from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError
from .models import (
    DBSession,
    Base,
    )


class RootFactory(object):

    # Additional ACLs loaded from the DB below
    __acl__ = [(Allow, Authenticated, 'view')]
    def __init__(self, request):
        pass


def getSettings(global_config, settings):
    # Secrets
    cp = ConfigParser.ConfigParser()
    cp.read(settings['awful.secrets_file'])
    for k,v in cp.items("app:main"):
        settings[k] = v

    scp = ConfigParser.SafeConfigParser()
    scp.read(global_config)
    for k,v in scp.items("app:safe"):
        settings[k] = v

    return settings


def checkout_listener(dbapi_con, con_record, con_proxy):
    try:
        try:
            dbapi_con.ping(False)
        except TypeError:
            dbapi_con.ping()
    except Exception, e:
        import sys
        print >> sys.stderr, "Error: %s (%s)" % (Exception, e)
        raise DisconnectionError()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings = getSettings(global_config['__file__'], settings)
    log = logging.getLogger(__name__)

    engine = engine_from_config(settings, 'sqlalchemy.')
    event.listen(engine, 'checkout', checkout_listener)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('user', '/user')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('signup', '/signup')
    config.add_route('help', '/help')
    config.add_route('ratings', '/ratings')
    config.add_route('places', '/places')
    config.add_route('factions', '/factions')
    config.add_route('test', '/test')
    config.add_renderer('json', JSON(indent=2))

    config.set_authentication_policy(
        AuthTktAuthenticationPolicy(settings['awful.cookie_token'], callback=local_groupfinder, max_age=604800)
        )

    config.set_authorization_policy(
        ACLAuthorizationPolicy()
        )

    config.scan()
    return config.make_wsgi_app()
