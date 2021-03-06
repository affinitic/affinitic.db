# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import os
import sys
import sqlalchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from zope.interface import classImplements
from affinitic.db.interfaces import IMetadata, IDatabase
from zope.event import notify
import grokcore.component as grok
from zope.sqlalchemy import ZopeTransactionExtension


SA_0_5_andmore = sqlalchemy.__version__ == 'svn' \
    or (int(sqlalchemy.__version__.split('.')[:2][0]) >= 0 and
        int(sqlalchemy.__version__.split('.')[:2][1]) >= 5)


class DB(grok.GlobalUtility):
    grok.implements(IDatabase)
    notifyInterface = None
    passFile = ''
    forceUnicode = False
    verbose = False
    createAll = True
    encoding = 'utf-8'
    _session = None
    persistentSession = False
    withZope = False
    engine_options = {}

    def __init__(self):
        self.configuredMappers = False

    @property
    def urlPass(self):
        moduleName = self.__class__.__module__
        module = sys.modules[moduleName]
        folder = os.path.dirname(os.path.abspath(module.__file__))
        fd = open(os.path.join(folder, self.passFile))
        fileContent = fd.read()
        fd.close()
        return fileContent.strip()

    def connect(self):
        if self.forceUnicode:
            self.engine = create_engine(self.url,
                                        convert_unicode=True,
                                        echo=self.verbose,
                                        encoding=self.encoding,
                                        **self.filtered_engine_options)
        else:
            self.engine = create_engine(self.url,
                                        echo=self.verbose,
                                        **self.filtered_engine_options)
        self.metadata = MetaData(self.engine)

    @property
    def filtered_engine_options(self):
        """ Return the engine options that are compatible with engine """
        options = self.engine_options
        if 'sqlite' in self.url and 'max_overflow' in options:
            del options['max_overflow']
        return options

    def setMappers(self):
        if not hasattr(self, 'metadata'):
            self.connect()
        classImplements(MetaData, IMetadata)
        notify(self.notifyInterface(self.metadata))
        if self.createAll:
            self.metadata.create_all(checkfirst=True)
        self.configuredMappers = True

    @property
    def url(self):
        raise NotImplemented("You must implement the url property")

    def _checkMappers(self):
        if not self.configuredMappers:
            self.connect()
            self.setMappers()

    @property
    def session(self):
        self._checkMappers()
        if self.persistentSession and self._session:
            return self._session
        sess = self.new_session(self.engine)
        if self.persistentSession:
            self._session = sess
        return sess

    def new_session(self, engine):
        if SA_0_5_andmore:
            extension = None
            if self.withZope:
                extension = ZopeTransactionExtension()
            return sessionmaker(bind=engine, autoflush=False,
                                extension=extension)()
        else:
            return sessionmaker(bind=engine, autoflush=False,
                                transactional=True)()

    @property
    def connection(self):
        self._checkMappers()
        return self.session.connection()

    def refresh(self):
        self.metadata.drop_all()
        self.metadata.create_all()
        self._checkMappers()
