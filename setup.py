from setuptools import setup, find_packages

try:
    from setuptools import setup, find_packages
    have_setuptools = True
except ImportError:
    from distutils.core import setup
    def find_packages():
        return ['corkscrew',]
    have_setuptools = False

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

if have_setuptools:
    add_keywords = dict( entry_points = \
                         { 'console_scripts': \
                           ['corkscrew = corkscrew.bin._corkscrew:entry', ]
                         }, )
else:
    add_keywords = dict( scripts = ['corkscrew'], )

setup(
    name         ='corkscrew',
    version      = '.1',
    description  = 'ooviews, settings, and basic authentication for flask',
    author       = 'mattvonrocketstein, in the gmails',
    url          = 'one of these days',
    license      = 'BSD License',
    package_dir  = {'': 'lib'},
    packages     = find_packages('lib'),
    long_description = __doc__,
    keywords = 'flask',
    platforms = 'any',
    zip_safe = False,
    include_package_data = True,
    classifiers = [
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Development Status :: 000 - Experimental',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Operating System :: OS Independent', ],
    cmdclass = {'build_py': build_py},
    **add_keywords
)
