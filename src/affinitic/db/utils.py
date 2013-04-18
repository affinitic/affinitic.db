# -*- coding: utf-8 -*-
import warnings
import sqlalchemy
import zope.deprecation
from sqlalchemy import __version__ as sa_version
try:
    from sqlalchemy.exceptions import SADeprecationWarning
    SADeprecationWarning  # Pyflakes fix
except ImportError:
    from sqlalchemy.exc import SADeprecationWarning

try:
    from sqlalchemy.util._collections import immutabledict
    immutabledict  # Pyflakes fix
except ImportError:
    immutabledict = dict

try:
    from sqlalchemy.databases.sqlite import SQLiteDialect
    SQLiteDialect  # Pyflakes fix
except:
    from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite as SQLiteDialect

try:
    from sqlalchemy.dialects.oracle.cx_oracle import OracleDialect_cx_oracle as OracleDialect
    OracleDialect  # Pyflakes fix
except:
    from sqlalchemy.databases.oracle import OracleDialect

try:
    from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2 as PgDialect
    PgDialect  # Pyflakes fix
except:
    from sqlalchemy.databases.postgres import PGDialect as PgDialect

try:
    from sqlalchemy.ext.declarative import DeferredReflection
    DeferredReflection  # Pyflakes fix
except ImportError:
    from affinitic.db.declarative import DeferredReflection


def remove_schema(tables):
    """ Removes all the references to schemas from the Declarative metadata """
    newtables = tables.copy()
    for table_key in newtables:
        table = tables.pop(table_key)
        if table.schema is not None:
            table.schema = None
        tables[table.name] = table
        for fk in get_fk_with_schema(table):
            fk._colspec = '.'.join(fk._colspec.split('.')[1:])
    return tables


def get_fk_with_schema(table):
    """ Returns a list with the foreign keys that depend on a schema """
    fk_list = []
    for col in [c for c in table.columns if c.foreign_keys]:
        fk_list.extend(
            [f for f in col.foreign_keys if len(f._colspec.split('.')) > 2])
    return fk_list


def initialize_declarative_mappers(declarativebase, metadata, reflection=True,
                                   relation=True):
    # Loops on the mapper for the relations
    while True:
        before_length = len(declarativebase.metadata.tables)
        for mapper in declaratives_mappers(declarativebase.metadata):
            if relation is False and mapper.has_active_relation() is False:
                mapper._relations_state = 'INACTIVE'
            else:
                mapper._relations_state = None
            mapper.init_relations()
        if before_length == len(declarativebase.metadata.tables):
            break

    # Avoid troubles with sqlite and the schemas
    tables = dict(declarativebase.metadata.tables)
    if isinstance(metadata.bind.dialect, SQLiteDialect):
        tables = remove_schema(tables)

    # Extends the metadata from the model
    new_tables = dict(metadata.tables)
    for table_key, table in tables.items():
        table.metadata = metadata
        new_tables[table_key] = table
    metadata.tables = immutabledict(new_tables)
    for mapper in declaratives_mappers(metadata):
        # no reflection on sqlite table
        if reflection and \
           not isinstance(metadata.bind.dialect, SQLiteDialect) and \
           issubclass(mapper, DeferredReflection):
            mapper.prepare(metadata.bind)
        # Ensure that a primary mapper is defined
        elif sqlalchemy.__version__.startswith('0.4'):
            if len(mapper.__mapper__._class_state.mappers.keys()) == 0:
                new_mapper = sqlalchemy.orm.mapper(mapper,
                                                   mapper.__table__)
                mapper.__mapper__ = new_mapper
        else:
            # the class_manager object is implemented since the version 0.5.x
            if not hasattr(mapper, '__mapper__') or \
               mapper.__mapper__ is not mapper.__mapper__.class_manager.mapper:
                mapper.__mapper__ = sqlalchemy.orm.mapper(mapper,
                                                          mapper.__table__)


def declaratives_mappers(metadata):
    # http://stackoverflow.com/questions/8956928/how-to-iterate-through-every-class-declaration-descended-from-a-particular-base/8957113#8957113
    #
    from affinitic.db.mapper import MappedClassBase
    import gc
    all_refs = gc.get_referrers(MappedClassBase)
    results = []
    for obj in all_refs:
        # __mro__ attributes are tuples
        # and if a tuple is found here, the given class is one of its members
        if (isinstance(obj, tuple) and
            # check if the found tuple is the __mro__ attribute of a class
            getattr(obj[0], "__mro__", None) is obj):
            results.append(obj[0])
    for klass in results:
        if hasattr(klass, '__table__') and \
           klass.__table__ in metadata.tables.values():
            yield klass


def initialize_defered_mappers(metadata):
    # Execute __declare__last__ for sqlalchemy 0.4
    for mapper in declaratives_mappers(metadata):
        if hasattr(mapper, '_create_relations'):
            mapper._create_relations()
        # http://docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html#declare-last
        if sa_version.startswith('0.4') and hasattr(mapper, '__declare_last__') is True:
            mapper.__declare_last__()


def deprecated_table_definition(replacement):
    def outer(oldfun):
        def inner(*args, **kwargs):
            if zope.deprecation.__show__():
                warnings.warn('The function is deprecated, you should use the mapper %s like this: %s.__table__' % (replacement, replacement.__name__),
                              DeprecationWarning, 2)
            return replacement.__table__
        return inner
    return outer


def disable_sa_deprecation_warnings():
    # turn off all deprecation warnings coming from SA
    warnings.filterwarnings("ignore", category=SADeprecationWarning)


def enable_sa_deprecation_warnings():
    # turn on all deprecation warnings coming from SA
    warnings.filterwarnings("always", category=SADeprecationWarning)


def engine_type(engine):
    if isinstance(engine.dialect, OracleDialect):
        return 'oracle'
    elif isinstance(engine.dialect, PgDialect):
        return 'pg'
    elif isinstance(engine.dialect, SQLiteDialect):
        return 'sqlite'
    else:
        raise ValueError('Unknown dialect')
