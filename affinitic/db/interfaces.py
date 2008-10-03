# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.interface import Interface
from zope.component.interfaces import IObjectEvent


class IPGDBInitialized(IObjectEvent):
    """DBInitialized event"""


class IOracleDBInitialized(IObjectEvent):
    """DBInitialized event"""


class IMetadata(Interface):
    """
    """


class IInteractionResult(Interface):
    """
    Marker interface for an Interaction Result
    """


class IDatabase(Interface):
    """
    """
