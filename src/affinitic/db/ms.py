# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

"""

from affinitic.db.event import MSSqlDBInitialized
from affinitic.db.db import DB
import grokcore.component as grok


class MSSqlDB(DB):
    grok.name('mssql')
    notifyInterface = MSSqlDBInitialized
    passFile = 'mspass'
    db = None

    @property
    def url(self):
        return 'mssql://%s@10.0.65.3:1216/%s' % (self.urlPass,
                                                 self.db)
