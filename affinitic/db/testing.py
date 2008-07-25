# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from unittest import TestCase
from zope.component import getUtility, getUtilitiesFor
from zope.configuration.config import ConfigurationMachine
from zope.configuration import xmlconfig
from affinitic.db.interfaces import IDatabase


def dbSetup(config_file, package):
    config = ConfigurationMachine()
    context = xmlconfig._getContext()
    xmlconfig.include(context, config_file, package)
    context.execute_actions()
    for name, utility in getUtilitiesFor(IDatabase):
        utility.setMappers()


class ZCMLLayer:

    def __init__(self, config_file, module, name, allow_teardown=False):
        self.config_file = config_file
        self.__module__ = module
        self.__name__ = name
        self.allow_teardown = allow_teardown

    def setUp(self):
        dbSetup(self.config_file, self.__module__)


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
