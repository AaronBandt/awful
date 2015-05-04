from pyramid.view import view_config
from pyramid.response import Response
from datetime import datetime
from datetime import timedelta
import arrow
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    get_nearby,
    )
from awfulweb.models import (
    DBSession,
    User,
    Rating,
    LastVisit,
    )


class PlaceResponse(object):
    name = ""
    place_id = ""
    avg = ""
    pa = ""

    def __init__(self, name, place_id, avg, pa):
        self.name = name
        self.place_id = place_id
        self.avg = avg
        self.pa = pa

def _place_response(name, place_id, avg, pa):
    response = PlaceResponse(name, place_id, avg, pa)
    return response


@view_config(route_name='home', permission='view', renderer='awfulweb:templates/home.pt')
def view_home(request):
    page_title = 'Become AWFUL.'
    au = get_authenticated_user(request)
    visit_threshold = int(request.registry.settings['awful.visit_threshold'])
    has_reviews = False
    display = False
    results = False
    current_lat = None
    current_lon = None
    places_response = []
    awfulites = []

#    request.response.set_cookie('lat',value='12345',max_age=604800,path='/')

    params = {
              'radius': request.registry.settings['awful.default_radius'],
             }
    for p in params:
        try:
            params[p] = request.params[p]
        except:
            pass

#    print request.cookies

    try:
        current_lat = request.cookies['current_lat']
        current_lon = request.cookies['current_lon']
    except:
        pass
    radius = params['radius']

    try:
        log.info('checking for ratings for user: %s' % au['login'])
        q = DBSession.query(Rating).filter(Rating.updated_by==au['login'])
        total = q.count()
        if total:
            has_reviews = True
            page_title = "Go eat something AWFUL with these people"
    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    if 'whereto.submitted' in request.POST:
        awfulites = request.POST.getall('awfulite')
        # always include the logged in user
        awfulites.append(au['login'])
        display = True
        page_title = "Go eat someplace AWFUL"

        print "Calculating places for these awfulites: ", awfulites

        # convert users to ids
        # FIXME: Query once with in_?
        awfulite_ids = []
        for a in awfulites:
            try:
                q = DBSession.query(User).filter(User.user_name==a)
                result = q.one()
                awfulite_ids.append(result.user_id)
            except Exception, e:
                conn_err_msg = e
                return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

        try:
            places = get_nearby(current_lat = current_lat, current_lon = current_lon, radius = radius)

            # Check the places and remove ones that have a last visit date
            # less than the threshold
            for p in places:
                for v in p.last_visit:
                    if v.user_id in awfulite_ids:
                        utc_server_now = arrow.utcnow().naive
                        if not v.date < utc_server_now - timedelta(days=visit_threshold):
                            log.info('REMOVING from results: %s' % (p.name))
                            # FIXME: need something better than just catching the exception
                            try:
                                places.remove(p)
                            except:
                                pass
    
            # Find all the ratings by the included AWFULites
            for p in places:
                ratings = {}
                log.debug('PLACE: %s' % (p.name))
                for r in p.ratings:
                    pa = None
                    if r.updated_by in awfulites:
                         log.debug('Rated by: %s Rating: %s' % (r.updated_by, r.rating))
                         ratings[r.updated_by] = r.rating
    
                if ratings:
                    avg = float("{0:.2f}".format(sum(ratings.values())/float(len(ratings))))
                    log.debug('Average: %s' % (avg))
                    if len(ratings) > 1:
                        pa = min(ratings, key=ratings.get)
                        log.debug('Biggest pain in the ass: %s' %(pa))
    
                    places_response.append(_place_response(p.name, p.place_id, avg, pa))
    
            # Sort by rating
            places_response.sort(key=lambda x: x.avg, reverse=True)

        except Exception, e:
            conn_err_msg = e
            return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    if 'lets_ride.submitted' in request.POST:
        awfulites = request.POST.getall('awfulite')
        place_id = request.POST.get('place_id')

        # Add a last visit record for each awfulite
        for a in awfulites:
            try:
                q = DBSession.query(User).filter(User.user_name==a)
                result = q.one()
                user_id = result.user_id
            except Exception, e:
                conn_err_msg = e
                return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

            # if they have a record update it, else create
            q = DBSession.query(LastVisit).filter(LastVisit.place_id==place_id, LastVisit.user_id==user_id)
            check = DBSession.query(q.exists()).scalar()
            utcnow = datetime.utcnow()
            if check:
                try:
                    log.info("Updating last_visit record for awfulite: %s for place_id: %s" % (a, place_id))
                    this_record = DBSession.query(LastVisit).filter(LastVisit.place_id==place_id, LastVisit.user_id==user_id).one()
                    this_record.date = utcnow
                    DBSession.flush()
                except Exception, e:
                    conn_err_msg = e
                    return Response(str(conn_err_msg), content_type='text/plain', status_int=500)
            else:
                try:
                    log.info("Adding last_visit record for awfulite: %s for place_id: %s" % (a, place_id))
                    create = LastVisit(place_id=place_id, user_id=user_id, date=utcnow)
                    DBSession.add(create)
                    DBSession.flush()
                except Exception, e:
                    conn_err_msg = e
                    return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    q = DBSession.query(User).filter(~(User.user_name==au['login']))
    all_users = q.all()
    
    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'has_reviews': has_reviews,
            'all_users': all_users,
            'display': display,
            'results': results,
            'places_response': places_response,
            'awfulites': awfulites,
            'current_lat': current_lat,
            'current_lon': current_lon,
            'radius': radius,
           }

