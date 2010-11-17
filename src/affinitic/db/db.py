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


SA_0_5_andmore = sqlalchemy.__version__ == 'svn' \
    or (int(sqlalchemy.__version__.split('.')[:2][0]) >= 0
        and int(sqlalchemy.__version__.split('.')[:2][1]) >= 5)


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

    def __init__(self):
        self.connect()
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
                                        encoding=self.encoding)
        else:
            self.engine = create_engine(self.url,
                                        echo=self.verbose)
        self.db = self.engine.connect()
        self.metadata = MetaData(self.engine)

    def setMappers(self):
        self.metadata.clear()
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
            self.setMappers()

    @property
    def session(self):
        self._checkMappers()
        if self.persistentSession and self._session:
            return self._session
        if SA_0_5_andmore:
            sess = sessionmaker(bind=self.engine, autoflush=False)()
        else:
            sess = sessionmaker(bind=self.engine, autoflush=False,
                                transactional=True)()
        if self.persistentSession:
            self._session = sess
        return sess

    @property
    def connection(self):
        self._checkMappers()
        return self.session.connection()

    def refresh(self):
        self.metadata.drop_all()
        self.metadata.create_all()
        self._checkMappers()
