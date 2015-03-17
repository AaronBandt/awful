from pyramid.view import view_config
from pyramid.response import Response
from datetime import datetime
import logging
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    )
from awfulweb.models import (
    DBSession,
    Place,
    )

@view_config(route_name='places', permission='view', renderer='awfulweb:templates/places.pt')
def view_places(request):
    page_title = 'You know this place will be AWFUL.'
    au = get_authenticated_user(request)

    if 'place.submitted' in request.POST:
        name = request.POST['name']

        print "Name: %s User: %s" % (name, au['login'])
        try:
            utcnow = datetime.utcnow()
            create = Place(name=name, updated_by=au['login'], created=utcnow, updated=utcnow)
            DBSession.add(create)
            DBSession.flush()
        except Exception, e:
            conn_err_msg = e
            return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    try:
        places = DBSession.query(Place).all()
    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'places': places,
           }

