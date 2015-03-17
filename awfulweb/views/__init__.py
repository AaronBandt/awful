from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound
from pyramid.session import signed_deserialize
import logging
from passlib.hash import sha512_crypt
from awfulweb.models import (
    DBSession,
    User,
    Group,
    )

log = logging.getLogger(__name__)


def site_layout():
    renderer = get_renderer("awfulweb:templates/global_layout.pt")
    layout = renderer.implementation().macros['layout']
    return layout


def local_groupfinder(userid, request):
    """ queries the db for a list of groups the user belongs to.
        Returns either a list of groups (empty if no groups) or None
        if the user doesn't exist. """

    groups = None
    try:
        user = DBSession.query(User).filter(User.user_name==userid).one()
        groups = user.get_all_assignments()
    except Exception, e:
        pass
        log.info("%s (%s)" % (Exception, e))

    return groups


def local_authenticate(login, password):
    """ Checks the validity of a username/password against what
        is stored in the database. """

    try: 
        q = DBSession.query(User)
        q = q.filter(User.user_name == login)
        db_user = q.one()
    except Exception, e:
        log.info("%s (%s)" % (Exception, e))
        # Should return invalid username here somehow
        pass

    try: 
        if sha512_crypt.verify(password, db_user.password):
            return [login]
    except Exception, e:
        log.info("%s (%s)" % (Exception, e))
        pass

    return None


def get_authenticated_user(request):
    """ Gets all the user information for an authenticated  user. Checks groups
        and permissions, and returns a dict of everything. """

    try:
        request_id = request.authenticated_userid
        user = DBSession.query(User).filter(User.user_name==request_id).one()
        user_id = user.user_id
        first = user.first_name
        last = user.last_name
        groups = local_groupfinder(request_id, request)
        first_last = "%s %s" % (first, last)
        auth = True
    except Exception, e:
        log.error("%s (%s)" % (Exception, e))
        (first_last, user_id, login, groups, first, last, auth, prd_auth, admin_auth, cp_auth) = ('', '', '', '', '', '', False, False, False, False)

    try:
        login = validate_username_cookie(request.cookies['un'], request.registry.settings['awful.cookie_token'])
    except:
        return HTTPFound('/logout?message=Your cookie has been tampered with. You have been logged out')

    # authenticated user
    au = {}
    au['user_id'] = user_id
    au['login'] = login
    au['groups'] = groups
    au['first'] = first
    au['last'] = last
    au['loggedin'] = auth
    au['first_last'] = first_last

    return (au)


def get_all_groups():
    """ Gets all the groups that are configured in
        the db and returns a dict of everything. """

    # Get the groups from the db
    group_perms = []
    r = DBSession.query(Group).all()
    for g in range(len(r)):
        ga = r[g].get_all_assignments()
        if ga:
            ga = tuple(ga)
            group_perms.append([r[g].group_name, ga])

    return(group_perms)


def format_user(user):
    # Make the name readable
    (last,first,junk) = user.split(',',2)
    last = last.rstrip('\\')
    last = last.strip('CN=')
    return(first,last)

def format_groups(groups):

    formatted = []
    for g in range(len(groups)):
        formatted.append(find_between(groups[g], 'CN=', ',OU='))
    return formatted

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def validate_username_cookie(cookieval, cookie_token):
    """ Returns the username if it validates. Otherwise throws
    an exception"""

    return signed_deserialize(cookieval, cookie_token)

