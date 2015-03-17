from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.session import signed_serialize
import logging
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    local_authenticate,
    )

@view_config(route_name='login', renderer='awfulweb:templates/login.pt')
@forbidden_view_config(renderer='awfulweb:templates/login.pt')
def login(request):
    page_title = 'Login'

    au = get_authenticated_user(request)

    if request.referer:
        referer_host = request.referer.split('/')[2]
    else:
        referer_host = None

    if request.referer and referer_host == request.host and request.referer.split('/')[3][:6] != 'logout' and request.referer.split('/')[3][:6] != 'signup':
        return_url = request.referer
    elif request.path != '/login':
        return_url = request.url
    else:
        return_url = '/'

    login = ''
    password = ''
    error = ''

    if 'form.submitted' in request.POST:
        login = request.POST['login']
        password = request.POST['password']

        data = local_authenticate(login, password)
            
        if data is not None:
            dn = data[0]
            encrypted = signed_serialize(login, request.registry.settings['awful.cookie_token'])
            headers = remember(request, dn)
            headers.append(('Set-Cookie', 'un=' + str(encrypted) + '; Max-Age=604800; Path=/'))

            return HTTPFound(request.POST['return_url'], headers=headers)
        else:
            error = 'Invalid credentials'

    if request.authenticated_userid:

        if request.path == '/login':
          error = 'You are already logged in'
          page_title = 'Already Logged In'
        else:
          error = 'You do not have permission to access this page'
          page_title = 'Access Denied'

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'return_url': return_url,
            'login': login,
            'password': password,
            'error': error,
           }
