""" hammock.runner

    TODO: not generic
"""
import platform
from report import report
from corkscrew.runner import tornado, flask

if platform.node() in ['dosojin']: # fixme: abstract
    report("Using flask default as server")
    run = flask
else:
    report("Using tornado as server")
    run = tornado
