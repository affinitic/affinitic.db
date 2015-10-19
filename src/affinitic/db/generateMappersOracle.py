# -*- coding: utf-8 -*-
"""
<+ MODULE +>
~~~~~~~~~~~~

Created by seb
:copyright: (c) 2015 by Affinitic SPRL
:license: GPL, see LICENCE.txt for more details.
"""
import os

f = open('exportSANITEL.sql', 'r')


def main():
    if not os.path.exists("generatedmapper"):
        os.makedirs("generatedmapper")
    primary_keys = searchPrimarykey()
    makeMapper(primary_keys)


def searchPrimarykey():
    """
    """
    primary_keys = []
    for line in f:
        line = line.lower()
        primary_keys_dict = {}

        if "create table" in line:
            table_name = line.split()
            table_name = table_name[2].split('.')
            table_name = table_name[1]

        if "primary key" in line:
            row = line.split()
            column = row[2]
            column = column.split('(', 1)
            column = column[1]
            column = column.split(')', 1)
            column = column[0]
            primary_keys_dict[table_name] = column
            table_name = ""
            primary_keys.append(primary_keys_dict)

    return primary_keys


def makeMapper(primary_keys):
    f.seek(0, 0)
    for line in f:
        line = line.lower()
        if "create table" in line:
            table_name = line.split()
            table_name = table_name[2].split('.')
            table_name = table_name[1]
            mapperfile = open("generatedmapper/" + table_name + ".py", 'w+r')
            generateTopFile(mapperfile, table_name)
            mapperfile.write('\n')
        else:
            if "primary key" not in line and ");" not in line:
                row = line.split()
                column_name = row[0]
                column_type = row[1]
                mapper = "    %s = sa.Column('%s'," % (column_name, column_name)
                if "number" in column_type:
                    mapper += "sa.Integer()"
                if "varchar" in column_type:
                    column_type = 'varchar'
                    max = row[1]
                    max_char = max.split('(', 1)
                    max_char = max_char[1]
                    max_char = max_char.split(')', 1)
                    max_char = max_char[0]
                    mapper += "sa.String(length=%s)" % (max_char)

                if "date" in column_type:
                    mapper += "sa.DateTime"

                for row in primary_keys:
                        if row.get(table_name):
                            if column_name == row[table_name]:
                                mapper += ", primary_key=True"
                if "not null" in line:
                    mapper += ", nullable=False)"
                if "not null" not in line:
                    mapper += ")"

                mapperfile.write('\n')
                mapperfile.write(mapper)
                mapperfile.write('\n')


def generateTopFile(mapperfile, table_name):
    top = """# -*- coding: utf-8 -*-
import sqlalchemy as sa
from arsia.db.oracle.mappers import SanitraceMappedClassBase
from arsia.db.oracle import DeclarativeBase """
    mapperfile.write(top)
    mapperfile.write('\n')
    mapperfile.write('\n')
    mapperfile.write('\n')
    classname = """class %s(DeclarativeBase, SanitraceMappedClassBase):""" % (table_name.title())
    mapperfile.write(classname)
    mapperfile.write('\n')
    other = """    __tablename__ = u'%s'
    __table_args__ = {'schema': 'sanitel'}"""\
                % (table_name)
    mapperfile.write(other)


if __name__ == '__main__':
    main()
