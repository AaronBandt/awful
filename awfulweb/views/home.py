from pyramid.view import view_config
from pyramid.response import Response
from datetime import datetime
from datetime import timedelta
import arrow
import urllib
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    _cs_api_query,
    SearchResult,
    )
from awfulweb.models import (
    DBSession,
    User,
    Rating,
    Place,
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
    page_title = 'I ate lunch once. It was AWFUL.'
    au = get_authenticated_user(request)
    has_reviews = False
    display = False
    results = False
    # number in days before next visit allowed.
    visit_threshold = 5
    places_response = []
    geo_places_ids = []
    cs_pub_code = request.registry.settings['awful.cs_pub_code']
    awfulites = []
#    awfulites = ['aaron.bandt@citygridmedia.com', 'user1@aaronbandt.com', 'julie@gmail.com']

    if 'whereto.submitted' in request.POST:
        awfulites = request.POST.getall('awfulite')
        display = True

        try:
            # get these settings from the form or fallback to config defaults
            # FIXME: should be able to move this to the main function with some creativity
            try:
                home_lat = request.POST['home_lat']
                home_lon = request.POST['home_lon']
                log.info("Got lat: %s lon: %s from browser" % (home_lat,home_lon))
            except:
                home_lat = request.registry.settings['awful.default_lat']
                home_lon = request.registry.settings['awful.default_lon']
                pass

            try:
                radius = request.POST['radius']
            except:
                radius = request.registry.settings['awful.default_radius']
                pass

            s = {'lat': home_lat, 'lon': home_lon, 'radius': radius}
            api_endpoint = '/content/places/v2/search/latlon?&format=json&rpp=50&type=restaurant&publisher=' + cs_pub_code
            req = api_endpoint + '&' + urllib.urlencode(s)
            resp = _cs_api_query(req)

            print "Number of responses: ", resp['results']['total_hits']
            total_pages = (resp['results']['total_hits'] / 50) + 1
            print "Total pages: ", total_pages
            for r in resp['results']['locations']:
                geo_places_ids.append(r['id'])

            # get the rest
            page = 2
            while page <= total_pages:
                new_req = req + '&page=' + str(page)
                log.info("requesting page: %i" % (page))
                resp = _cs_api_query(new_req)
                for r in resp['results']['locations']:
                    geo_places_ids.append(r['id'])
                page += 1

#            geo_places_ids = ['613773250', '731112440']
            q = DBSession.query(Place).filter(Place.cs_id.in_(geo_places_ids))
            places = q.all()
            for p in places:
                print "Name: ", p.name
                print "CS ID: ", p.cs_id

            # convert users to ids
            awfulite_ids = []
            for a in awfulites:
                try:
                    q = DBSession.query(User).filter(User.user_name==a)
                    result = q.one()
                    awfulite_ids.append(result.user_id)
                except Exception, e:
                    conn_err_msg = e
                    return Response(str(conn_err_msg), content_type='text/plain', status_int=500)
    
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
            'places_response': places_response,
            'awfulites': awfulites,
           }

