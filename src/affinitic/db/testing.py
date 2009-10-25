# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from unittest import TestCase
from zope.component import getUtility, getUtilitiesFor
from affinitic.db.interfaces import IDatabase
from zope.app.testing.functional import ZCMLLayer as _ZCMLLayer
from sqlalchemy.orm import clear_mappers


class ZCMLLayer(_ZCMLLayer):

    def __init__(self, *args, **kwargs):
        kwargs['allow_teardown'] = True
        _ZCMLLayer.__init__(self, *args, **kwargs)

    def setUp(self):
        _ZCMLLayer.setUp(self)
        for name, utility in getUtilitiesFor(IDatabase):
            utility.setMappers()

    def tearDown(self):
        _ZCMLLayer.tearDown(self)
        clear_mappers()


class BaseTestCase(TestCase):
    """
    Basic Test setup
    """

    @property
    def pg(self):
        return getUtility(IDatabase, 'postgres')

    def setUp(self):
        self.pg.metadata.create_all()

    def tearDown(self):
        self.pg.metadata.drop_all()
