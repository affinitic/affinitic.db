# -*- coding: utf-8 -*-

from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import Interface

import grokcore.component as grok

from affinitic.db import utils


class ITypeConverter(Interface):
    """Utility interface to convert data to the desired sql output"""

    def convert(self, value):
        """Return a string with the value formated for a sql statement"""


class TypeConverter(grok.GlobalUtility):
    grok.provides(ITypeConverter)


class DefaultTypeConverter(TypeConverter):
    grok.name('default')

    def convert(self, value):
        if value is None:
            return u'null'
        return str(value)


class TextTypeConverter(TypeConverter):
    grok.name('Text')

    def convert(self, value):
        if value is None:
            return u'null'
        replacements = (
            ("'", "''"),
            ("%", "%%"),
        )
        for replacement in replacements:
            value = value.replace(replacement[0], replacement[1])
        return u"'%s'" % value


class StringTypeConverter(TextTypeConverter):
    grok.name('String')


class DateTypeConverter(TextTypeConverter):
    grok.name('DATE')

    def convert(self, value):
        if value is None:
            return u'null'
        return u"'%s'" % str(value)


class DateAliasTypeConverter(DateTypeConverter):
    grok.name('Date')


class DatetimeTypeConverter(DateTypeConverter):
    grok.name('DATETIME')


class DatetimeAliasTypeConverter(DateTypeConverter):
    grok.name('DateTime')


class RowConverter(object):

    def __init__(self, mapper, row):
        self.mapper = mapper
        self.row = row

    @property
    def tablename(self):
        return utils.get_tablename(self.mapper)

    @property
    def columns(self):
        return self.mapper.__table__._columns

    def get_converter(self, column):
        converter_name = column.type.__class__.__name__
        converter = queryUtility(ITypeConverter, name=converter_name)
        if not converter:
            converter = getUtility(ITypeConverter, name='default')
        return converter

    @property
    def insert_statement(self):
        sql_statement = u'INSERT INTO %s (%s) VALUES (%s);'
        columns = []
        values = []
        for column in self.columns:
            converter = self.get_converter(column)
            columns.append(column.name)
            raw_value = getattr(self.row, column.name)
            values.append(converter.convert(raw_value))
        return sql_statement % (
            self.tablename,
            u', '.join(columns),
            u', '.join(values),
        )
