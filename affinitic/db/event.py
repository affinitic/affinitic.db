# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.interface import implements
from affinitic.db.interfaces import IPGDBInitialized


class PGDBInitialized(object):
    implements(IPGDBInitialized)

    def __init__(self, objectToAdapt):
        self.object = objectToAdapt
