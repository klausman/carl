#!/usr/bin/env python

from distutils.core import setup

setup(name='Carl',
      version='0.4',
      license = "GNU GPL v2",
      description='A simple rsync logfile analyzer',
      author='Tobias Klausmann',
      author_email='klausman-carl@schwarzvogel.de',
      url='http://www.schwarzvogel.de/software-misc.shtml',
      py_modules=['Accounts', 'Sessions'],
      scripts=['Carl.py'],
      data_files=[("share/doc/carl-0.4/",['README', 'COPYING'])]
     )
