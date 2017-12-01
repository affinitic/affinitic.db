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
    replacements = (
        ("'", "''"),
        ("%", "%%"),
    )

    def convert(self, value):
        if value is None:
            return u'null'
        for replacement in self.replacements:
            value = value.replace(replacement[0], replacement[1])
        return u"'%s'" % value


class StringTypeConverter(TextTypeConverter):
    grok.name('String')


class OraTextTypeConverter(TextTypeConverter):
    grok.name('Text_oracle')
    replacements = (
        ("'", "''"),
    )


class OraStringTypeConverter(OraTextTypeConverter):
    grok.name('String_oracle')


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


class OraDateTypeConverter(TextTypeConverter):
    grok.name('DATE_oracle')

    def convert(self, value):
        if value is None:
            return u'null'
        return "TO_DATE('%s', 'YYYY-MM-DD HH24:MI:SS')" % str(value)


class OraDateAliasTypeConverter(OraDateTypeConverter):
    grok.name('Date_oracle')


class OraDatetimeTypeConverter(OraDateTypeConverter):
    grok.name('DATETIME_oracle')


class OraDatetimeAliasTypeConverter(OraDateTypeConverter):
    grok.name('DateTime_oracle')


class RowConverter(object):

    def __init__(self, mapper, row, engine=None):
        self.mapper = mapper
        self.row = row
        self.engine = engine

    @property
    def tablename(self):
        return utils.get_tablename(self.mapper)

    @property
    def columns(self):
        return self.mapper.__table__._columns

    def get_converter(self, column):
        converter_name = column.type.__class__.__name__
        converter_fallback = [converter_name, 'default']
        if self.engine is not None:
            converter_fallback.insert(
                0,
                '%s_%s' % (converter_name, self.engine),
            )
        for name in converter_fallback:
            converter = queryUtility(ITypeConverter, name=name)
            if converter:
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
