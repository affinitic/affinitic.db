# -*- coding: utf-8 -*-

from affinitic.db import utils


class DependencyOrder(object):
    """Dependency order using Kahn topological sorting"""

    def __init__(self, elements):
        self.elements = {}
        for e in elements:
            self.elements[e] = []

    def add_dependency(self, element, dependency):
        if dependency not in self.elements:
            raise ValueError('Unknown dependency')
        self.elements[dependency].append(element)

    def topological_sort(self):
        in_degree = {}
        for e in self.elements:
            in_degree[e] = 0

        # Traverse dependencies to fill indegrees
        for k, v in self.elements.items():
            for e in [element for element in v if element in in_degree]:
                in_degree[e] += 1

        # Create a queue with all elements with indegree of 0
        queue = [k for k, v in in_degree.items() if v == 0]
        ordered_elements = []

        while queue:
            u = queue.pop(0)
            ordered_elements.append(u)
            for i in self.elements[u]:
                in_degree[i] -= 1
                if in_degree[i] == 0:
                    queue.append(i)

        if len(ordered_elements) != len(self.elements):
            raise ValueError('There is a circular dependency')
        else:
            return ordered_elements


class OrderedMappers(object):
    """
    Class that order a list of mappers to respect foreign keys constraints
    """

    def __init__(self, mappers):
        self.mappers = mappers
        self._mappers = {}
        self._tables = {}
        for mapper in self.mappers:
            self._tables[utils.get_tablename(mapper)] = mapper
        self._ordered_mappers = DependencyOrder(mappers)

    def _process_mappers(self):
        for mapper in self.mappers:
            self._update_mapper_dependencies(mapper)

    def _update_mapper_dependencies(self, mapper):
        table = mapper.__table__
        for fk in table._foreign_keys:
            fk_tablename = utils.get_tablename(utils.get_table(fk))
            if fk_tablename not in self._tables.keys():
                continue
            if utils.get_tablename(mapper) == fk_tablename:
                continue
            self._ordered_mappers.add_dependency(
                mapper,
                self._tables[fk_tablename],
            )

    @property
    def ordered_mappers(self):
        self._process_mappers()
        return self._ordered_mappers.topological_sort()
