# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from affinitic.db.pg import PGDB
from affinitic.db.interfaces import IPGDBInitialized
import grokcore.component as grok
from sqlalchemy import (MetaData, Table, Column, Integer, Sequence,
                        Text)
from sqlalchemy.orm import mapper


class Animal(object):
    pass


@grok.subscribe(MetaData, IPGDBInitialized)
def dbAdded(metadata, event):
    animalTable = Table('Animal', metadata,
                 Column(u'animal_pk', Integer(),
                        Sequence('animal_seq'), primary_key=True),
                 Column(u'animal_name', Text()))
    mapper(Animal, animalTable)


class MyPGDB(PGDB):

    @property
    def url(self):
        return 'sqlite:///:memory:'
