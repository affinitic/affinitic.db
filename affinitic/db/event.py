# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.interface import implements
from affinitic.db.interfaces import IPGDBInitialized, IOracleDBInitialized, \
                                    IMSSqlDBInitialized


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
