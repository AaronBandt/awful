from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.sql import func
from sqlalchemy import or_
from sqlalchemy import desc
from sqlalchemy.sql import label
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    )
from awfulweb.models import (
    DBSession,
    User,
    Group,
    Place,
    Rating,
    )

@view_config(route_name='test', permission='view', renderer='awfulweb:templates/test.pt')
def view_test(request):
    page_title = 'test.'
    au = get_authenticated_user(request)
    results = False

    results=['Cafe Primo',
             'Tender Greens',
             'Five Guys',
             'Burger Lounge'
            ]

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'results': results,
           }

