from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPConflict
from pyramid.security import remember, forget
from pyramid.session import signed_serialize, signed_deserialize
from pyramid.response import Response
from sqlalchemy.sql import exists
from datetime import datetime
import logging
import os.path
import binascii
from passlib.hash import sha512_crypt
from awfulweb.views import (
    get_authenticated_user,
    site_layout,
    log,
    )
from awfulweb.models import (
    DBSession,
    User,
    UserGroupAssignment,
    Group,
    )

@view_config(route_name='factions', permission='view', renderer='awfulweb:templates/factions.pt')
def view_faction(request):
    page_title = 'AWFUL people to go to lunch with.'
    au = get_authenticated_user(request)

    if 'faction.create' in request.POST:
        name = request.POST['name']

        try:
            utcnow = datetime.utcnow()
            create = Group(group_name=name, updated_by=au['login'], created=utcnow, updated=utcnow)
            DBSession.add(create)
            DBSession.flush()
            group_id = create.group_id
            
            # Add the current user to the faction on initial create
            create = UserGroupAssignment(group_id=group_id, user_id=au['user_id'], updated_by=au['login'], created=utcnow, updated=utcnow)
            DBSession.add(create)
            DBSession.flush()

        except Exception as ex:
            if type(ex).__name__ == 'IntegrityError':
                log.info('Group already exists in the db, please edit instead.')
                # Rollback
                DBSession.rollback()
                # FIXME: Return a nice page
                #return HTTPConflict('Group already exists in the db, please edit instead.')
            else:
                raise
                # FIXME not trapping correctly
                DBSession.rollback()
                error_msg = ("Failed to create the faction: (%s)" % (ex))
                log.error(error_msg)

    if 'faction.join' in request.POST:
        group_id = request.POST['group_id']

        try:
            utcnow = datetime.utcnow()
            # Add the current user to the faction
            join = UserGroupAssignment(group_id=group_id, user_id=au['user_id'], updated_by=au['login'], created=utcnow, updated=utcnow)
            DBSession.add(join)
            DBSession.flush()
        except Exception as ex:
                error_msg = ("Failed to join faction (%s)" % (ex))
                log.error(error_msg)

    if 'faction.leave' in request.POST:
        group_id = request.POST['group_id']

        try:
            utcnow = datetime.utcnow()
            # Remove the current user from the faction
            leave = DBSession.query(UserGroupAssignment).filter(UserGroupAssignment.group_id==group_id, UserGroupAssignment.user_id==au['user_id']).one()
            DBSession.delete(leave)
            DBSession.flush()
        except Exception as ex:
                error_msg = ("Failed leave faction (%s)" % (ex))
                log.error(error_msg)

    try:
        factions = DBSession.query(Group).all()
    except Exception, e:
        conn_err_msg = e
        return Response(str(conn_err_msg), content_type='text/plain', status_int=500)

    # update the groups we're in
    au = get_authenticated_user(request)

#    for f in factions:
#        print f.user_group_assignments
#        for a in f.user_group_assignments:
#            print a.user.user_name

    return {'layout': site_layout(),
            'page_title': page_title,
            'au': au,
            'factions': factions,
           }

