from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.sql import exists
from sqlalchemy import and_
from datetime import datetime
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    get_nearby,
    contains,
    )
from awfulweb.models import (
    DBSession,
    Place,
    Rating,
    )

@view_config(route_name='ratings', permission='view', renderer='awfulweb:templates/ratings.pt')
def view_ratings(request):
    page_title = 'Places you know are AWFUL.'
    au = get_authenticated_user(request)
    perpage = 10
    rated = None
    unrated = None
    no_unrated = False

    params = {'sort_type': 'a',
              'sort_order': 'asc',
              'show': 'unrated',
              'start': 0,
              'home_lat': None,
              'home_lon': None,
              'radius': request.registry.settings['awful.default_radius'],
             }
    for p in params:
        try:
            params[p] = request.params[p]
        except:
            pass

    sort_type = params['sort_type']
    sort_order = params['sort_order']
    show = params['show']
    offset = int(params['start'])
    home_lat = params['home_lat']
    home_lon = params['home_lon']
    radius = params['radius']

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

    # FIXME: this is ugly
    geo_places = get_nearby(request)
    geo_place_ids = []
    for g in geo_places:
        geo_place_ids.append(g.cs_id)
    
    try:
        if show == 'unrated':
            unrated = []
            q = DBSession.query(Place).filter(~exists().where(and_(Place.place_id == Rating.place_id, Rating.updated_by == au['login'])))
            results = q.order_by(getattr(Place.name, sort_order)()).limit(perpage).offset(offset)
            # Only show what's close
            for r in results:
                if contains(geo_places, lambda x: x.cs_id == r.cs_id):
                    unrated.append(r)

            total = len(unrated)

            # Show rated if there is nothing unrated
            if total == 0:
                show = 'rated'
                # This doesn't work if you explicitly ask for rated
                no_unrated = True
            else:
                page_title = 'Places that might be AWFUL.'

        if show == 'rated':
           q = DBSession.query(Rating)
           q = q.filter(Rating.updated_by==au['login'])
           q = q.join(Place)
           q = q.filter(Place.cs_id.in_(geo_place_ids))
           total = q.count()

           if sort_type == 'a':
               rated = q.order_by(getattr(Place.name, sort_order)()).limit(perpage).offset(offset)
           else:
               rated = q.order_by(getattr(Rating.rating, sort_order)()).limit(perpage).offset(offset)

    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    if not home_lat:
        page_title = 'Tracking your AWFUL position.'

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'perpage': perpage,
            'show': show,
            'offset': offset,
            'sort_type': sort_type,
            'sort_order': sort_order,
            'total': total,
            'rated': rated,
            'unrated': unrated,
            'no_unrated': no_unrated,
            'home_lat': home_lat,
            'home_lon': home_lon,
            'radius': radius,
           }
