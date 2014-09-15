from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='xdash.boards',
      version=version,
      description="Xdash Tool user dashboards",
      long_description=open("README.txt").read() + "\n" +
      open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          ],
      keywords='',
      author='Kreativkombinat GbR',
      author_email='cb@ade25.de',
      url='http://dist.ade25.de',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['xdash'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.app.dexterity [grok, relations]',
          'plone.app.relationfield',
          'plone.namedfile [blobs]',
          'plone.formwidget.contenttree',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
