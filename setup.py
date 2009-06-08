from setuptools import setup, find_packages
import os

version = '0.2dev'

setup(name='affinitic.db',
      version=version,
      description="db initialization generic code",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Jean-Fran\xc3\xa7ois Roche',
      author_email='jfroche@affinitic.be',
      url='http://svn.affinitic.be/python/affinitic.db',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['affinitic'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'sqlalchemy>=0.4,<0.5beta',
          'grokcore.component',
          'zope.testing',
          'zope.security',
          # -*- Extra requirements: -*-
          'pysqlite'
      ],
      entry_points={
            'console_scripts': [
                'test = affinitic.db.tests.runalltests:main']})
