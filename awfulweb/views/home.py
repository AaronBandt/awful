from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.sql import func
from sqlalchemy import desc
from sqlalchemy.sql import label
import datetime
import arrow
from dateutil import tz
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
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
    avg = ""
    pa = ""

    def __init__(self, name, avg, pa):
        self.name = name
        self.avg = avg
        self.pa = pa

def _place_response(name, avg, pa):
    response = PlaceResponse(name, avg, pa)
    return response


@view_config(route_name='home', permission='view', renderer='awfulweb:templates/home.pt')
def view_home(request):
    page_title = 'I ate lunch once. It was AWFUL.'
    au = get_authenticated_user(request)
    has_reviews = False
    display = False
    results = False
    visit_threshold = 1
    awfulite = ['aaron.bandt@citygridmedia.com', 'user1@aaronbandt.com', 'julie@gmail.com']

    if 'whereto_submitted' in request.POST:
        p = request.POST.getall('awfulite')

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

        q = DBSession.query(Place)
        places = q.all()

        # Check the places and remove ones that have a last visit date
        # less than the threshold
        for p in places:
            for v in p.last_visit:
#                utc_date = arrow.get(v.date)
#                localized_db_date = utc_date.to('US/Pacific')
#                print "LOCALIZED DB DATE IS: ", localized_db_date
                utc_server_now = arrow.utcnow().naive
                if not v.date < utc_server_now-datetime.timedelta(days=visit_threshold):
                    print 'REMOVING from results: ', p.name
                    places.remove(p)

        # Find all the ratings by the included AWFULites
        places_response = []
        for p in places:
            ratings = {}
            print "PLACE: ", p.name
            for r in p.ratings:
                pa = None
                if r.updated_by in awfulite:
                     print "Rated by: %s Rating: %s" % (r.updated_by, r.rating)
                     ratings[r.updated_by] = r.rating

            if ratings:
                avg = float("{0:.2f}".format(sum(ratings.values())/float(len(ratings))))
                print "Average: %s" % (avg)
                if len(ratings) > 1:
                    pa = min(ratings, key=ratings.get)
                    print "Biggest pain in the ass: ", pa

                places_response.append(_place_response(p.name, avg, pa))

        # Sort by rating
        places_response.sort(key=lambda x: x.avg, reverse=True)


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
           }

