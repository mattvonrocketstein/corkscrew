#!/usr/bin/env python
""" corkscrew/setup.py
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
install_requires = [
    'reporting',
    'goulash',

    'configparser',
    'demjson',
    'humanize',
    'Importing',
    'flask-mongoengine',
    'flask',
    'flask-cache',
    'flask_sijax',
    'Flask-AutoIndex',
    'flask-debugtoolbar',
    'pymongo',
    'pygments',
    'mongoengine',
    'tornado',
]

base_url = 'https://github.com/mattvonrocketstein/corkscrew/'
setup(
    author               = 'mattvonrocketstein',
    author_email         = '$author@gmail',
    name                 = 'corkscrew',
    description          = 'ooviews, settings, auth & more for flask',
    install_requires     = install_requires,
    version              = __version__,
    url                  = base_url,
    include_package_data = True,
    packages             = ['corkscrew'],
    keywords             = ['flask'],
    entry_points         = dict(
        console_scripts=['corkscrew = corkscrew.bin._corkscrew:entry',])
    )
