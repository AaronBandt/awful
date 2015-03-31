from pyramid.view import view_config
from pyramid.response import Response
from datetime import datetime
import logging
import urllib
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    _cs_api_query,
    SearchResult,
    get_nearby,
    contains,
    )
from awfulweb.models import (
    DBSession,
    Place,
    )

# requests is chatty
logging.getLogger("requests").setLevel(logging.WARNING)


@view_config(route_name='places', permission='view', renderer='awfulweb:templates/places.pt')
def view_places(request):
    page_title = 'You know this place will be AWFUL.'
    au = get_authenticated_user(request)
    result_count = None
    search = False
    search_results = []
    cs_pub_code = request.registry.settings['awful.cs_pub_code']

    params = {'home_lat': None,
              'home_lon': None,
              'radius': None,
             }
    for p in params:
        try:
            params[p] = request.params[p]
        except:
            pass

    home_lat = params['home_lat']
    home_lon = params['home_lon']
    radius = params['radius']

    if 'place_search.submitted' in request.POST:
        name = request.POST['name']

        # get these settings from the form or fallback to config defaults
        # FIXME: should be able to move this to the main function with some creativity
        try:
            home_lat = request.POST['home_lat']
            home_lon = request.POST['home_lon']
            log.info("View got lat: %s lon: %s from browser" % (home_lat,home_lon))
        except:
            home_lat = request.registry.settings['awful.default_lat']
            home_lon = request.registry.settings['awful.default_lon']
            log.info("View using default lat: %s lon: %s" % (home_lat,home_lon))
            pass

        try:
            radius = request.POST['radius']
            log.info("View got radius: %s from browser" % (radius))
        except:
            radius = request.registry.settings['awful.default_radius']
            log.info("View using default radius: %s" % (radius))
            pass

        s = {'what': name, 'lat': home_lat, 'lon': home_lon, 'radius': radius}
        api_endpoint = '/content/places/v2/search/latlon?type=restaurant&format=json&publisher=' + cs_pub_code
        req = api_endpoint + '&' + urllib.urlencode(s)
        resp = _cs_api_query(req)

        search = True
        print "Number of responses: ", resp['results']['total_hits']

        # get all the places so we can remove ones fromt he search 
        # that have already been added to the AWFUL db.
        # FIXME: This is not effficient. Also misleading in the seatch results.
        # Might be better to just catch the exception when trying to add a 
        # place that exists.
        q = DBSession.query(Place)
        places = q.all()

        for r in resp['results']['locations']:
            if not contains(places, lambda x: x.cs_id == r['id']):
                # Don't show places that are flagged as closed
                if not r['business_operation_status'] == 0:
                    search_results.append(SearchResult(r['name'], 
                                                      r['id'],
                                                      r['latitude'],
                                                      r['longitude'],
                                                      r['address']['street'],
                                                      r['address']['city'],
                                                      r['address']['state'],
                                                      r['address']['postal_code'],
                                                      r['phone_number'],
                                                      r['website']
                                                     )
                                        )

        result_count = len(search_results)

    if 'place_select.submitted' in request.POST:
        name = request.POST['name']
        cs_id = request.POST['cs_id']
        home_lat = request.POST['home_lat']
        home_lon = request.POST['home_lon']

        log.info("Name: %s cs_id: %s User: %s" % (name, cs_id, au['login']))
        # Add it to the db
        try:
            utcnow = datetime.utcnow()
            create = Place(name=name, cs_id=cs_id, lat=home_lat, lon=home_lon, updated_by=au['login'], created=utcnow, updated=utcnow)
            DBSession.add(create)
            DBSession.flush()
        except Exception, e:
            conn_err_msg = e
            return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    try:
        places = get_nearby(request)
    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    if not home_lat:
        page_title = 'Tracking your AWFUL position.'

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'places': places,
            'result_count': result_count,
            'search': search,
            'search_results': search_results,
            'cs_pub_code': cs_pub_code,
            'home_lat': home_lat,
            'home_lon': home_lon,
            'radius': radius,
           }

