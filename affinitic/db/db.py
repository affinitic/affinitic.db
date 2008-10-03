# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from zope.interface import classImplements
from affinitic.db.interfaces import IMetadata, IDatabase
from zope.event import notify
import os
import sys
import grokcore.component as grok


class DB(grok.GlobalUtility):
    grok.implements(IDatabase)
    notifyInterface = None
    passFile = ''

    def __init__(self):
        self.connect()
        self.configuredMappers= False

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
        self.engine = create_engine(self.url)
        self.db = self.engine.connect()
        self.metadata = MetaData(self.engine)

    def setMappers(self):
        self.metadata.clear()
        classImplements(MetaData, IMetadata)
        notify(self.notifyInterface(self.metadata))
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
        return sessionmaker(bind=self.engine, autoflush=False,
                            transactional=True)()

    @property
    def connection(self):
        self._checkMappers()
        return self.session.connection()

    def refresh(self):
        self.metadata.drop_all()
        self.metadata.create_all()
        self._checkMappers()
