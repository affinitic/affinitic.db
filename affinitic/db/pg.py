# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""

from affinitic.db.event import PGDBInitialized
from affinitic.db.db import DB
import grokcore.component as grok
import os

USER = os.popen('whoami').read().strip()


class PGDB(DB):
    grok.name('postgres')
    notifyInterface = PGDBInitialized
    passFile = 'pgpass'

    @property
    def url(self):
        return 'postgres://%s:%s@localhost:5432/arsia' % (USER, self.urlPass)
