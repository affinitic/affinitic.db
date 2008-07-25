# -*- coding: utf-8 -*-
"""
affinitic.db

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import os
import unittest
import affinitic.db
testModule = affinitic.db.tests
from zope.configuration.name import resolve

def main():
    TestRunner = unittest.TextTestRunner
    suite = unittest.TestSuite()
    tests = os.listdir(os.path.dirname(testModule.__file__))
    tests = [n[:-3] for n in tests if n.startswith('test') and \
                                      n.endswith('.py')]

    for test in tests:
        m = resolve(testModule.__name__+'.'+test)
        if hasattr(m, 'test_suite'):
            suite.addTest(m.test_suite())
    TestRunner().run(suite)

if __name__ == '__main__':
    main()
