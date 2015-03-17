from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.sql import func
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
    Rating,
    )

@view_config(route_name='home', permission='view', renderer='awfulweb:templates/home.pt')
def view_home(request):
    page_title = 'I ate lunch once. It was AWFUL.'
    au = get_authenticated_user(request)
    has_reviews = False
    display = False
    results = False

    if 'whereto_submitted' in request.POST:
        p = request.POST.getall('included')

        q = DBSession.query(Rating,
            label('average', func.avg(Rating.rating))).filter(Rating.updated_by.in_(p)).group_by(Rating.place_id).order_by(desc('average'))
        results = q.all()

        display = True

    try:
        log.info('checking for ratings for user: %s' % au['login'])
        q = DBSession.query(Rating).filter(Rating.updated_by==au['login'])
        total = q.count()
        if total:
            has_reviews = True

    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    q = DBSession.query(User)
    all_users = q.all()

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'has_reviews': has_reviews,
            'all_users': all_users,
            'display': display,
            'results': results,
           }

