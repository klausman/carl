#!/usr/bin/env python

from distutils.core import setup

setup(name='carl',
      version='0.8',
      license = "GNU GPL v2",
      description='An rsync logfile analyzer',
      author='Tobias Klausmann',
      author_email='klausman-carl@schwarzvogel.de',
      url='http://www.schwarzvogel.de/software-misc.shtml',
      py_modules=['Accounts', 'Sessions'],
      scripts=['Carl.py'],
      data_files=[("share/doc/carl-%s/" % (version), ['COPYING', 'README'])]
     )
