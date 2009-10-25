# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.testing import doctest
import unittest
from zope.component import getUtilitiesFor
from affinitic.db.interfaces import IDatabase
from sqlalchemy.orm import clear_mappers
from Products.Five import zcml


def setUp(self):
    import affinitic.db.tests
    zcml.load_config('psqltesting.zcml', affinitic.db.tests)
    for name, utility in getUtilitiesFor(IDatabase):
        utility.metadata.create_all()


def tearDown(self):
    for name, utility in getUtilitiesFor(IDatabase):
        utility.metadata.drop_all()
    clear_mappers()


def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
           'psql.txt',
           package='affinitic.db.tests',
           setUp=setUp,
           tearDown=tearDown,
           optionflags=(doctest.ELLIPSIS |
                         doctest.NORMALIZE_WHITESPACE))])
