from setuptools import setup, find_packages
import os

version = '0.10'

setup(name='affinitic.db',
      version=version,
      description="db initialization generic code",
      long_description=open("README.rst").read() + "\n" +
      open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='',
      author='Jean-Francois Roche',
      author_email='jfroche@affinitic.be',
      url='http://svn.affinitic.be/python/affinitic.db',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['affinitic'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'sqlalchemy',
          'pysqlite',
          'grokcore.component',
          'zope.deprecation',
          'zope.security',
          'zope.sqlalchemy',
          'zope.testing',
      ],
      extras_require=dict(
          caching=['dogpile.cache'],
      ),
      entry_points={
          'console_scripts': ['test = affinitic.db.tests.runalltests:main']})
