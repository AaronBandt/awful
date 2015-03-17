from pyramid.view import view_config
import logging
from awfulweb.views import (
    site_layout,
    )

@view_config(route_name='help', renderer='awfulweb:templates/help.pt')
def help(request):

    page_title = 'Login'

    return {'layout': site_layout(),
            'page_title': page_title,
            }


