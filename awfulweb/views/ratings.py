from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.sql import exists
from sqlalchemy import and_
from datetime import datetime
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    )
from awfulweb.models import (
    DBSession,
    Place,
    Rating,
    )

@view_config(route_name='ratings', permission='view', renderer='awfulweb:templates/ratings.pt')
def view_ratings(request):
    page_title = 'Your AWFUL ratings.'
    au = get_authenticated_user(request)
    perpage = 10

    params = {'sort_type': 'a',
              'sort_order': 'a',
              'start': 0
             }
    for p in params:
        try:
            params[p] = request.params[p]
        except:
            pass

    sort_type = params['sort_type']
    sort_order = params['sort_order']
    offset = int(params['start'])

    if 'rating.submitted' in request.POST:
        place_id = request.POST['place_id']
        rating = request.POST['rating']

        try:
            q = DBSession.query(Rating).filter(Rating.place_id==place_id, Rating.updated_by==au['login'])
            rating_check = DBSession.query(q.exists()).scalar()
            if rating_check:
                # update
                log.info("UPDATE rating: %s place_id: %s user: %s" % (rating, place_id, au['login']))
                utcnow = datetime.utcnow()
                update = DBSession.query(Rating).filter(Rating.place_id==place_id, Rating.updated_by==au['login']).one()
                update.rating = rating
                DBSession.flush()
            else:
                # Create
                log.info("CREATE rating: %s place_id: %s user: %s" % (rating, place_id, au['login']))
                utcnow = datetime.utcnow()
                create = Rating(place_id=place_id, rating=rating, updated_by=au['login'], created=utcnow, updated=utcnow)
                DBSession.add(create)
                DBSession.flush()
        except Exception, e:
            conn_err_msg = e
            return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    try:
        q = DBSession.query(Rating)
        q = q.filter(Rating.updated_by==au['login'])
        q = q.join(Place)
        total_rated = q.count()
        # FIXME: feels like this should be better
        if sort_type == 'a':
            if sort_order == 'd':
                rated = q.order_by(Place.name.desc()).limit(perpage).offset(offset)
            else:
                rated = q.order_by(Place.name.asc()).limit(perpage).offset(offset)
        else:
            if sort_order == 'd':
                rated = q.order_by(Rating.rating.desc()).limit(perpage).offset(offset)
            else:
                rated = q.order_by(Rating.rating.asc()).limit(perpage).offset(offset)


        q = DBSession.query(Place).filter(~exists().where(and_(Place.place_id == Rating.place_id, Rating.updated_by == au['login'])))
        total_unrated = q.count()
        if sort_order == 'd':
            unrated = q.order_by(Place.name.desc()).limit(perpage).offset(offset)
        else:
            unrated = q.order_by(Place.name.asc()).limit(perpage).offset(offset)

#        unrated.sort(key=lambda x: x.name, reverse=False)

    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'perpage': perpage,
            'offset': offset,
            'sort_type': sort_type,
            'sort_order': sort_order,
            'total_rated': total_rated,
            'total_unrated': total_unrated,
            'rated': rated,
            'unrated': unrated,
           }
