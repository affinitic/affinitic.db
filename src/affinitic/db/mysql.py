# encoding: utf-8
"""
affinitic.db

Created by mpeeters
Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""

from affinitic.db.db import DB
from affinitic.db.event import MySQLDBInitialized

import grokcore.component as grok
import os

USER = os.popen('whoami').read().strip()


class MySQLDB(DB):
    grok.name('mysql')
    notifyInterface = MySQLDBInitialized
    passFile = 'mysqlpass'
    db = None

    @property
    def url(self):
        return 'mysql://%s:%s@localhost:3306/%s' % (USER, self.urlPass,
                                                    self.db)
