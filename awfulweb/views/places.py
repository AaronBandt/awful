from pyramid.view import view_config
from pyramid.response import Response
from datetime import datetime
import logging
import requests
import urllib
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    )
from awfulweb.models import (
    DBSession,
    Place,
    )

# requests is chatty
logging.getLogger("requests").setLevel(logging.WARNING)



class SearchResult(object):

    def __init__(self, name, cs_id, lat, lon, addr_street, addr_city, addr_state, addr_zip, phone, website):
        self.name = name
        self.cs_id = cs_id
        self.lat = lat
        self.lon = lon
        self.addr_street = addr_street
        self.addr_city = addr_city
        self.addr_state = addr_state
        self.addr_zip = addr_zip
        self.phone = phone
        self.website = website


def _cs_api_query(req):

    # Hardcode for now
    verify_ssl = False
    api_protocol = 'http'
    api_host = 'api.citygridmedia.com'

    # This becomes the api call
    api_url = (api_protocol
               + '://'
               + api_host
               + req)

    logging.info('Requesting data from API: %s' % api_url)
    r = requests.get(api_url, verify=verify_ssl)

    if r.status_code == requests.codes.ok:

        logging.debug('Response data: %s' % r.json())
        return r.json()

    else:

        logging.info('There was an error querying the API: '
                      'http_status_code=%s,reason=%s,request=%s'
                      % (r.status_code, r.reason, api_url))
        return None


@view_config(route_name='places', permission='view', renderer='awfulweb:templates/places.pt')
def view_places(request):
    page_title = 'You know this place will be AWFUL.'
    au = get_authenticated_user(request)
    result_count = None
    search = False
    search_results = []

    if 'place_search.submitted' in request.POST:
        name = request.POST['name']

        # get these settings from the form or fallback to config defaults
        try:
            home_lat = request.POST['home_lat']
            home_lon = request.POST['home_lon']
            logging.info("Got lat: %s lon: %s from browser" % (home_lat,home_lon))
        except:
            home_lat = request.registry.settings['awful.default_lat']
            home_lon = request.registry.settings['awful.default_lon']
            pass

        try:
            radius = request.POST['radius']
        except:
            radius = request.registry.settings['awful.default_radius']
            pass

        s = {'what': name, 'lat': home_lat, 'lon': home_lon, 'radius': radius}
        api_endpoint = '/content/places/v2/search/latlon?&format=json&publisher=' + request.registry.settings['awful.cs_pub_code']
        req = api_endpoint + '&' + urllib.urlencode(s)
        resp = _cs_api_query(req)

        search = True
        print "Number of responses: ", resp['results']['total_hits']
        for r in resp['results']['locations']:
            result_count = resp['results']['total_hits']
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
            

    if 'place_select.submitted' in request.POST:
        name = request.POST['name']
        cs_id = request.POST['cs_id']

        logging.info("Name: %s cs_id: %s User: %s" % (name, cs_id, au['login']))
        # Add it to the db
        try:
            utcnow = datetime.utcnow()
            create = Place(name=name, cs_id=cs_id, updated_by=au['login'], created=utcnow, updated=utcnow)
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
            'result_count': result_count,
            'search': search,
            'search_results': search_results,
           }

