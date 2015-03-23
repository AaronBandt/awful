import arrow
from dateutil import tz
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import (
    Column,
    Integer,
    Text,
    TIMESTAMP,
    ForeignKey,
    )
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from zope.sqlalchemy import ZopeTransactionExtension


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

def _localize_date(obj):
        utc = arrow.get(obj)
        zone = 'US/Pacific' # FIXME: This needs to be configurable somehow
        return  utc.to(tz.gettz(zone)).format('YYYY-MM-DD HH:mm:ss ZZ')


class User(Base):
    __tablename__ = 'users'
    user_id          = Column(Integer, primary_key=True, nullable=False)
    user_name        = Column(Text, nullable=False) # email address
    first_name       = Column(Text, nullable=True)
    last_name        = Column(Text, nullable=True)
    salt             = Column(Text, nullable=False)
    password         = Column(Text, nullable=False)
    updated_by       = Column(Text, nullable=False)
    created          = Column(TIMESTAMP, nullable=False)
    updated          = Column(TIMESTAMP, nullable=False)

    @hybrid_method
    def get_all_assignments(self):
        ga = []
        for a in self.user_group_assignments:
            ga.append(a.group.group_name)
        return ga

    @hybrid_property
    def localize_date_created(self):
        local = _localize_date(self.created)
        return local

    @hybrid_property
    def localize_date_updated(self):
        local = _localize_date(self.updated)
        return local


class UserGroupAssignment(Base):
    __tablename__ = 'user_group_assignments'
    user_group_assignment_id = Column(Integer, primary_key=True, nullable=False)
    group_id                = Column(Integer, ForeignKey('groups.group_id'), nullable=False)
    user_id                 = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_by              = Column(Text, nullable=False)
    created                 = Column(TIMESTAMP, nullable=False)
    updated                 = Column(TIMESTAMP, nullable=False)
    user                    = relationship("User", backref=backref('user_group_assignments'))
    group                   = relationship("Group", backref=backref('user_group_assignments'))


class Group(Base):
    __tablename__ = 'groups'
    group_id         = Column(Integer, primary_key=True, nullable=False)
    group_name       = Column(Text, nullable=False)
    updated_by       = Column(Text, nullable=False)
    created          = Column(TIMESTAMP, nullable=False)
    updated          = Column(TIMESTAMP, nullable=False)

    @hybrid_method
    def get_all_assignments(self):
        ga = []
        for a in self.group_assignments:
            ga.append(a.group_perms.perm_name)
        return ga

    @hybrid_property
    def localize_date_created(self):
        local = _localize_date(self.created)
        return local

    @hybrid_property
    def localize_date_updated(self):
        local = _localize_date(self.updated)
        return local


class Place(Base):
    __tablename__ = 'places'
    place_id         = Column(Integer, primary_key=True, nullable=False)
    cs_id            = Column(Integer, nullable=False)
    name             = Column(Text, nullable=False)
    updated_by       = Column(Text, nullable=False)
    created          = Column(TIMESTAMP, nullable=False)
    updated          = Column(TIMESTAMP, nullable=False)

    @hybrid_property
    def localize_date_created(self):
        local = _localize_date(self.created)
        return local

    @hybrid_property
    def localize_date_updated(self):
        local = _localize_date(self.updated)
        return local


class Rating(Base):
    __tablename__ = 'ratings'
    rating_id       = Column(Integer, primary_key=True, nullable=False)
    place_id        = Column(Integer, ForeignKey('places.place_id'), nullable=False)
    rating          = Column(Integer, nullable=False)
    updated_by      = Column(Text, nullable=False)
    created         = Column(TIMESTAMP, nullable=False)
    updated         = Column(TIMESTAMP, nullable=False)
    place           = relationship("Place", backref=backref('ratings'))


class LastVisit(Base):
    __tablename__ = 'last_visit'
    last_visit_id   = Column(Integer, primary_key=True, nullable=False)
    place_id        = Column(Integer, ForeignKey('places.place_id'), nullable=False)
    user_id         = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date            = Column(TIMESTAMP, nullable=False)
    place           = relationship("Place", backref=backref('last_visit'))


