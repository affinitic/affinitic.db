# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""

from affinitic.db.event import OracleDBInitialized
from affinitic.db.db import DB
import grokcore.component as grok


class OracleDB(DB):
    grok.name('oracle')
    notifyInterface = OracleDBInitialized
    passFile = 'orapass'
    db = None

    @property
    def url(self):
        return 'oracle://%s@%s' % (self.urlPass,
                                      self.db)
