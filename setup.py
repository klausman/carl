#!/usr/bin/env python
"""Setup data for Carl"""
from distutils.core import setup

__version__ = "0.9"

setup(name='carl',
      version=__version__,
      license="GNU GPL v2",
      description='An rsync logfile analyzer',
      author='Tobias Klausmann',
      author_email='klausman-carl@schwarzvogel.de',
      url='http://www.schwarzvogel.de/software-misc.shtml',
      py_modules=['Accounts', 'Sessions'],
      scripts=['Carl.py'],
      data_files=[
          ("share/doc/carl-%s/" % (__version__), ['COPYING', 'README'])]
      )
