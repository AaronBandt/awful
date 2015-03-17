from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPConflict
from pyramid.security import remember
from pyramid.session import signed_serialize
from datetime import datetime
import logging
from passlib.hash import sha512_crypt
from awfulweb.views import (
    site_layout,
    local_authenticate,
    log,
    )
from awfulweb.models import (
    DBSession,
    User,
    )

@view_config(route_name='signup', renderer='awfulweb:templates/signup.pt')
def view_signup(request):
    page_title = 'Signup'

    user_name = None
    password = None
    error = ''

    if 'signup_submitted' in request.POST:

        user_name = request.POST.get('user_name')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        log.info('Recieved registration request for: %s' % user_name)

        try:
            utcnow = datetime.utcnow()
            salt = sha512_crypt.genconfig()[17:33]
            encrypted_password = sha512_crypt.encrypt(password, salt=salt)
            create = User(user_name=user_name, first_name=first_name, last_name=last_name, salt=salt, password=encrypted_password, updated_by=user_name, created=utcnow, updated=utcnow)
            DBSession.add(create)
            DBSession.flush()

            # log in the new user
            log.info("logging in new user: %s" % user_name)
            data = local_authenticate(user_name, password)

            dn = data[0]
            encrypted = signed_serialize(user_name, request.registry.settings['awful.cookie_token'])
            headers = remember(request, dn)
            headers.append(('Set-Cookie', 'un=' + str(encrypted) + '; Max-Age=604800; Path=/'))
    
            return HTTPFound('/', headers=headers)
 
        except Exception as ex:
            # raise
            if type(ex).__name__ == 'IntegrityError':
                log.info('User already exists in the db: %s' % user_name)
                error = ('Email address already taken: %s' % user_name)
                # Rollback
                DBSession.rollback()
            else:
                raise
                # FIXME not trapping correctly
                DBSession.rollback()
                error_msg = ("Failed to create user (%s)" % (ex))
                log.error(error_msg)

    return {'layout': site_layout(),
            'page_title': page_title,
            'password': password,
            'error': error,
           }
