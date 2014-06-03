# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import time
try:
    from sqlalchemy import event
except ImportError:
    # the event module is implemented since sqlalchemy 0.7
    event = None
from sqlalchemy.engine import Engine
from zope.interface import implements
from affinitic.db.log import log_long_query
from affinitic.db.interfaces import IMSSqlDBInitialized
from affinitic.db.interfaces import IMySQLDBInitialized
from affinitic.db.interfaces import IOracleDBInitialized
from affinitic.db.interfaces import IPGDBInitialized


class PGDBInitialized(object):
    implements(IPGDBInitialized)

    def __init__(self, objectToAdapt):
        self.object = objectToAdapt


class OracleDBInitialized(object):
    implements(IOracleDBInitialized)

    def __init__(self, objectToAdapt):
        self.object = objectToAdapt


class MSSqlDBInitialized(object):
    implements(IMSSqlDBInitialized)

    def __init__(self, objectToAdapt):
        self.object = objectToAdapt


class MySQLDBInitialized(object):
    implements(IMySQLDBInitialized)

    def __init__(self, object_to_adapt):
        self.object = object_to_adapt


def register_logging():
    if event is None:
        raise ImportError(u'The event module is implemented on SQLAlchemy '
                          u'0.7 and higher')

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context,
                              executemany):
        context._query_start_time = time.time()

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context,
                             executemany):
        total = time.time() - context._query_start_time
        log_long_query(conn.engine, total, statement, parameters)
