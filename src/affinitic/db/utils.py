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


def initialize_declarative_mappers(declarative_metadata, metadata,
                                   reflection=True, relation=True):
    # Backward compatibility
    if not hasattr(declarative_metadata, 'tables'):
        declarative_metadata = declarative_metadata.metadata
        warnings.warn('Please provide the metadata instead of the '
                      'DeclarativeBase class', DeprecationWarning, 2)
    # Loops on the mapper for the relations
    while True:
        before_length = len(declarative_metadata.tables)
        for mapper in declaratives_mappers(declarative_metadata):
            if relation is False and mapper.has_active_relation() is False:
                mapper._relations_state = 'INACTIVE'
            elif mapper._relations_state == 'INACTIVE':
                mapper._relations_state = None
            mapper.init_relations()
        if before_length == len(declarative_metadata.tables):
            break

    # Avoid troubles with sqlite and the schemas
    tables = dict(declarative_metadata.tables)
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
        if verify_mapper(mapper, metadata) is False:
            continue
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
        if isinstance(obj, tuple) \
           and getattr(obj[0], "__mro__", None) is obj:
            # check if the found tuple is the __mro__ attribute of a class
            results.append(obj[0])
    for klass in results:
        if hasattr(klass, '__table__') and \
           klass.__table__.key in [metadata.tables[k].key for k in
                                   metadata.tables.keys()]:
            yield klass


def initialize_defered_mappers(metadata):
    # Execute __declare__last__ for sqlalchemy 0.4
    ignored_tables = []
    for mapper in declaratives_mappers(metadata):
        # http://docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html#declare-last
        if verify_mapper(mapper, metadata) is False:
            continue
        if mapper._create_table is False:
            tname = '.'.join([e for e in [mapper.__table__.schema,
                                          mapper.__table__.name] if e])
            ignored_tables.append(tname)
        if sa_version.startswith('0.4') and hasattr(mapper, '__declare_last__') is True:
            mapper.__declare_last__()
        if hasattr(mapper, '_create_relations'):
            mapper._create_relations()
    # Fix defaults for tests
    if metadata.bind.name == 'sqlite':
        if sqlalchemy.__version__.startswith('0.4'):
            set_sqlite_defaults(metadata)
    # Avoid an error with the immutabledict from SA 0.8
    tables = dict(metadata.tables)
    for tname in ignored_tables:
        del tables[tname]
    metadata.tables = tables


def verify_mapper(mapper, metadata):
    """Ensure that the mapper is related to the given metadata"""
    tname = '.'.join([e for e in [mapper.__table__.schema,
                                  mapper.__table__.name] if e])
    return metadata.tables.get(tname) == mapper.__table__


def deprecated_table_definition(path):
    def outer(oldfun):
        def inner(*args, **kwargs):
            module_path, name = path.split(':')
            module = __import__(module_path, {}, {}, ['*'])
            replacement = getattr(module, name)
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


# http://stackoverflow.com/questions/12274814/functools-wraps-for-python-2-4
WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__doc__')
WRAPPER_UPDATES = ('__dict__',)


def wraps(wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=WRAPPER_UPDATES):
    def partial(func, *args, **kwds):
        return lambda *fargs, **fkwds: func(*(args + fargs), **dict(kwds, **fkwds))

    def update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS,
                       updated=WRAPPER_UPDATES):
        for attr in assigned:
            setattr(wrapper, attr, getattr(wrapped, attr))
        for attr in updated:
            getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
        return wrapper
    return partial(update_wrapper, wrapped=wrapped,
                   assigned=assigned, updated=updated)


class combomethod(object):
    """
    Decoractor that enables us to define a classmethod and an instance method
    with the same name
    """

    def __init__(self, method):
        self.method = method

    def __get__(self, obj=None, objtype=None):
        @wraps(self.method)
        def _wrapper(*args, **kwargs):
            if obj is not None:
                return self.method(obj, *args, **kwargs)
            else:
                return self.method(objtype, *args, **kwargs)
        return _wrapper


def set_sqlite_defaults(metadata):
    for mapper in declaratives_mappers(metadata):
        for col in mapper.__table__.columns:
            default = getattr(col, 'default', None)
            if isinstance(default, sqlalchemy.PassiveDefault):
                default_mapping = {'true': True, 'false': False}
                default_value = default_mapping.get(default.arg, default.arg)
                col.default = sqlalchemy.ColumnDefault(default_value)


def get_table(fk):
    """Return the table associate to the given foreign key"""
    remote_column = getattr(fk, '_column', getattr(fk, 'column'))
    return remote_column.table


def get_tablename(obj):
    """Return the tablename (with the schema) for the given mapper or table"""
    if isinstance(obj, sqlalchemy.Table):
        name = obj.name
        if obj.schema:
            name = '%s.%s' % (obj.schema, name)
        return name
    name = obj.__tablename__
    table_args = getattr(obj, '__table_args__', {})
    if isinstance(table_args, tuple):
        table_args = table_args[1]
    if table_args.get('schema'):
        name = u'%s.%s' % (table_args['schema'], name)
    return name
