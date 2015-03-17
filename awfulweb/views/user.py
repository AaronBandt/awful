from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from passlib.hash import sha512_crypt
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    )
from awfulweb.models import (
    DBSession,
    User,
    Rating,
    )

@view_config(route_name='user', permission='view', renderer='awfulweb:templates/user.pt')
def view_user(request):

    au = get_authenticated_user(request)
    page_title = 'User Data'
    change_pw = False

    if 'user.submitted' in request.POST:
        email_address = request.POST['email_address']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password = request.POST['password']

        # Need some security checking here
        if email_address != au['login']:
            print "Naughty monkey"
        else:
            # Update
            log.info('UPDATE: email_address=%s,first_name=%s,last_name=%s,password=%s'
                     % (email_address,
                       first_name,
                       last_name,
                       'pass'))
            try:
                user = DBSession.query(User).filter(User.user_name==email_address).one()
                user.first_name = first_name
                user.last_name = last_name
                if password:
                    log.info('Changing password for: %s' % email_address)
                    salt = sha512_crypt.genconfig()[17:33]
                    encrypted_password = sha512_crypt.encrypt(password, salt=salt)
                    user.salt = salt
                    user.password = encrypted_password
                    DBSession.flush()
                    return_url = '/logout?message=Your password has been changed successfully. Log in again.'
                    return HTTPFound(return_url)

                DBSession.flush()

            except Exception, e:
                pass
                log.info("%s (%s)" % (Exception, e))

    # Get the changes
    au = get_authenticated_user(request)
    subtitle = au['first_last']

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'subtitle': subtitle,
            'change_pw': change_pw,
           }
