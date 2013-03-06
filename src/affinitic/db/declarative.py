# -*- coding: utf-8 -*-
from sqlalchemy import Table
from sqlalchemy.orm import mapper


class DeferredReflection(object):
    """A helper class for construction of mappings based on
    a deferred reflection step.

    Normally, declarative can be used with reflection by
    setting a :class:`.Table` object using autoload=True
    as the ``__table__`` attribute on a declarative class.
    The caveat is that the :class:`.Table` must be fully
    reflected, or at the very least have a primary key column,
    at the point at which a normal declarative mapping is
    constructed, meaning the :class:`.Engine` must be available
    at class declaration time.

    The :class:`.DeferredReflection` mixin moves the construction
    of mappers to be at a later point, after a specific
    method is called which first reflects all :class:`.Table`
    objects created so far.   Classes can define it as such::

        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.ext.declarative import DeferredReflection
        Base = declarative_base()

        class MyClass(DeferredReflection, Base):
            __tablename__ = 'mytable'

    Above, ``MyClass`` is not yet mapped.   After a series of
    classes have been defined in the above fashion, all tables
    can be reflected and mappings created using
    :meth:`.DeferredReflection.prepare`::

        engine = create_engine("someengine://...")
        DeferredReflection.prepare(engine)

    The :class:`.DeferredReflection` mixin can be applied to individual
    classes, used as the base for the declarative base itself,
    or used in a custom abstract class.   Using an abstract base
    allows that only a subset of classes to be prepared for a
    particular prepare step, which is necessary for applications
    that use more than one engine.  For example, if an application
    has two engines, you might use two bases, and prepare each
    separately, e.g.::

        class ReflectedOne(DeferredReflection, Base):
            __abstract__ = True

        class ReflectedTwo(DeferredReflection, Base):
            __abstract__ = True

        class MyClass(ReflectedOne):
            __tablename__ = 'mytable'

        class MyOtherClass(ReflectedOne):
            __tablename__ = 'myothertable'

        class YetAnotherClass(ReflectedTwo):
            __tablename__ = 'yetanothertable'

        # ... etc.

    Above, the class hierarchies for ``ReflectedOne`` and
    ``ReflectedTwo`` can be configured separately::

        ReflectedOne.prepare(engine_one)
        ReflectedTwo.prepare(engine_two)

    .. versionadded:: 0.8

    """
    @classmethod
    def prepare(cls, engine):
        """Reflect all :class:`.Table` objects for all current
        :class:`.DeferredReflection` subclasses"""
        table = cls._sa_decl_prepare(cls.__table__, engine)
        if hasattr(cls, '_class_state'):  #SA 0.4
            del cls._class_state
        else:
            cls.__mapper__.dispose()
        cls.__mapper__ = mapper(cls, table)
        cls.__table__ = table

    @classmethod
    def _sa_decl_prepare(cls, local_table, engine):
        # autoload Table, which is already
        # present in the metadata.  This
        # will fill in db-loaded columns
        # into the existing Table object.
        if local_table is not None:
            return Table(local_table.name,
                local_table.metadata,
                autoload=True,
                autoload_with=engine,
                useexisting=True)
