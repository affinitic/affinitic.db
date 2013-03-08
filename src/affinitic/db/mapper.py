# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm import object_session
from affinitic.db.utils import disable_sa_deprecation_warnings, enable_sa_deprecation_warnings, engine_type


class Proxy(dict):
    """ Dict-Proxy for mapped objects providing
        attribute-style access.
    """

    def __init__(self, obj):
        super(dict, self).__init__()
        self.update(obj.__dict__.copy())
        for attr in getattr(obj, 'proxied_properties', ()):
            self[attr] = getattr(obj, attr)

        # patch:
        if hasattr(self, '_sa_instance_state'):
            del self['_sa_instance_state']
        if hasattr(self, '_state'):
            del self['_state']
        # old:
        #del self['_sa_instance_state']

    def __getattribute__(self, name):
        if name in dict.keys(self):
            return self.get(name)

        return super(dict, self).__getattribute__(name)

    def __getattr__(self, name, default=None):
        if name in dict.keys(self):
            return self.get(name, default)
        return super(dict, self).__getattr__(name, default)


class MappedClassBase(object):
    """
    Mapper base class
    """
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, **kw):
        """ accepts keywords arguments used for initialization of
            mapped attributes/columns.
        """

        self.wrapper = None
        for k, v in kw.items():
            setattr(self, k, v)

    def clone(self):
        """ Create a  pristine copy.
            Use this method if you need to reinsert a copy of the current
            mapper instance back into the database.
        """

        d = dict()
        for col in self.c.keys():
            d[col] = getattr(self, col)
        return self.__class__(**d)

    def asDict(self):
        """ Returns current object as a dict"""
        return Proxy(self)

    def getMapper(self, name):
        """ Return a mapper associated with the current mapper.
            If this mapper represents a table A having a relationship
            to table B then the mapper for B can be obtained through
            self.getMapper('B'). This method is useful if you don't want
            to pass the wrapper around this the wrapper is officially
            the only way to get hold of a mapper by name. See also
            http://groups.google.com/group/sqlalchemy/browse_thread/thread/18fb2e2818bdc032/5c2dfd71679925cb#5c2dfd71679925cb
        """
        try:
            return class_mapper(self.__class__).get_property(name).mapper.class_
        except AttributeError:
            return class_mapper(self.__class__).props[name].mapper.class_

    @classmethod
    def _session(cls):
        raise NotImplementedError

    @property
    def session(self):
        obj_session = object_session(self)
        if obj_session is not None:
            return obj_session
        return self.__class__._session()

    def update(self, flush=True, commit=False):
        """ Update the current instance into the session """
        sess = self.session
        sess.update(self)
        if flush is True:
            sess.flush()
        if commit is True:
            sess.commit()

    def insert(self, flush=True, commit=False):
        """ Save the current instance into the session """
        sess = self.session
        disable_sa_deprecation_warnings()
        sess.add(self)
        enable_sa_deprecation_warnings()
        if flush is True:
            sess.flush()
        if commit is True:
            sess.commit()

    def save_or_update(self, flush=True, commit=False):
        """ Save or update the current instance into the session """
        sess = self.session
        sess.add(self)
        if flush is True:
            sess.flush()
        if commit is True:
            sess.commit()

    # Aliases
    save = insert
    add = insert

    @classmethod
    def _engine_type(cls):
        return engine_type(cls._session().bind)

    @classmethod
    def _build_filter(cls, operator=sa.and_, **kwargs):
        filters = []
        for key, value in kwargs.items():
            column = getattr(cls, key)
            filters.append(column == value)
        return operator(*filters)

    @classmethod
    def exists(cls, **kwargs):
        session = cls._session()
        if cls._engine_type() == 'oracle':
            # oracle doesn't handle 'select from ...' queries
            return session.query(cls).filter('rownum = 1').filter(cls._build_filter(**kwargs)).count() == 1
        return session.query(sa.exists().where(cls._build_filter(**kwargs))).scalar()

    @classmethod
    def get(cls, **kwargs):
        return cls._session().query(cls).filter(cls._build_filter(**kwargs)).all()

    @classmethod
    def first(cls, **kwargs):
        return cls._session().query(cls).filter(cls._build_filter(**kwargs)).first()
