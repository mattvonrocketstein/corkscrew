#!/usr/bin/env python
""" setup.py for corkscrew
"""
import os, sys
from setuptools import setup

# make sure that finding packages works, even
# when setup.py is invoked from outside this dir
this_dir = os.path.dirname(os.path.abspath(__file__))
if not os.getcwd()==this_dir:
    os.chdir(this_dir)

# make sure we can import the version number so that it doesn't have
# to be changed in two places. corkscrew/__init__.py is also free
# to import various requirements that haven't been installed yet
sys.path.append(os.path.join(this_dir, 'corkscrew'))
from version import __version__
sys.path.pop()


setup(
    name         = 'corkscrew',
    description  = 'ooviews, settings, and basic authentication for flask',
    version      = __version__,
    author       = 'mattvonrocketstein',
    author_email = '$author@gmail',
    url          = 'https://github.com/mattvonrocketstein/corkscrew/',
    download_url = 'https://github.com/mattvonrocketstein/corkscrew/tarball/0.1',
    include_package_data = True,
    packages     = ['corkscrew'],
    keywords     = ['flask'],
    entry_points = \
    { 'console_scripts': \
      ['corkscrew = corkscrew.bin._corkscrew:entry', ]
      },
)
