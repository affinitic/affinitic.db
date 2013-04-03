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


class Relation(object):
    """
    Relation decorator for the declarative mappers
    The relation method defined with this decorator must return an sqlalchemy
    relation object and the relation name will be the same as the method name.

    The declaration of the relations are made by the __declare_last__ method of
    the class MappedClassBase.

    Example
    -------
    @Relation
    def monster(cls):
        from monster import Monster
        return sqlalchemy.orm.relation(Monster, lazy=False)
    """

    def __init__(self, method):
        self.method = method
        self.relation_name = method.func_name
        # Register the decorator
        self.decorator = self.__class__

    def __call__(self):
        """ Returns a dictionary with the relation and his name """
        return {self.relation_name: self.method.__call__(self.cls)}

    def __get__(self, instance, cls):
        self.cls = cls
        self.obj = instance

        return self.__call__


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
        sess.add(self)
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

    def delete(self, flush=True, commit=False):
        """ Delete the current instance into the session """
        sess = self.session
        sess.delete(self)
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
    def get(cls, options=[], order_by=[], **kwargs):
        session = cls._session()
        query = session.query(cls)
        query = query.options(options)
        if order_by:
            query = query.order_by(order_by)
        return query.filter(cls._build_filter(**kwargs)).all()

    @classmethod
    def count(cls, options=[], **kwargs):
        session = cls._session()
        query = session.query(cls)
        query = query.options(options)
        return query.filter(cls._build_filter(**kwargs)).count()

    sa_get = get

    @classmethod
    def first(cls, options=[], **kwargs):
        session = cls._session()
        query = session.query(cls)
        query = query.options(options)
        return query.filter(cls._build_filter(**kwargs)).first()

    @classmethod
    def init_relations(cls):
        """ Initialize the relations if that's necessary """
        if cls._inactive_relations is True:
            return
        cls._relations_dict = getattr(cls, '_relations_dict', {})
        cls._active_relations = getattr(cls, '_active_relations', [])
        cls._create_relations()
        # Removes the active relations after the creation to avoid problems
        # with the redeclaration of the mapper
        cls._active_relations = []

    @classmethod
    def declare_relations(cls, relations_list):
        """
        Declares a list of relations
        ex: Mapper.declare_relations(['a', 'b'])
        """
        for relation in relations_list:
            cls.declare_relation(relation)

    @classmethod
    def declare_relation(cls, relation_name):
        """ Declares a single relation ex: Mapper.declare_relation('a') """
        cls._active_relations = getattr(cls, '_active_relations', [])
        cls._active_relations.append(relation_name)

    @classmethod
    def _create_relations(cls):
        """ Creates the relations on the mapper """
        # Creates the dict with all the relations
        for relation in cls._get_relations():
            cls._relations_dict.update(getattr(cls, relation)())
        declared_relations = {}
        for relation in cls._active_relations or cls._relations_dict.keys():
            if relation not in cls._relations_dict:
                raise ValueError('Unknown relation "%s" for the table "%s"' % (
                    relation, cls.__tablename__))
            declared_relations[relation] = cls._relations_dict.get(relation)
        cls.__mapper__.add_properties(declared_relations)

    @classmethod
    def _get_relations(cls):
        """ Returns the relations defined with the Relation decorator """
        disable_sa_deprecation_warnings()
        relations = []
        for method in cls.__dict__.values():
            if hasattr(method, 'decorator') and method.decorator == Relation:
                relations.append(method.relation_name)
        enable_sa_deprecation_warnings()
        return relations

    @classmethod
    def has_active_relation(cls):
        """ Verifies if there is declared relations """
        return len(getattr(cls, '_active_relations', [])) > 0

    @classmethod
    def truncate(cls, restart=False):
        """ Delete all from table """
        if cls._engine_type() == 'pg':
            sess = cls._session()
            tablename = cls.__tablename__
            if cls.__table__.schema is not None:
                tablename = '%s.%s' % (cls.__table__.schema, tablename)
            options = list()
            if restart is True:
                options.append('RESTART IDENTITY')

            query = "TRUNCATE table %(table)s %(options)s;" % {
                'table': tablename,
                'options': ' '.join(options)}
            sess.execute(query)
            sess.commit()
        else:
            raise NotImplementedError("Truncate not supported yet with this database type")
