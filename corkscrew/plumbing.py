""" corkscrew.plumbing

    a few very lightweight middleware-ish things
"""
from flask import g
from flask import session, request

registry = []

def before_request():
    """ each request and look up the current user """
    g.user = None
    print request.url
    if request.values:
        print request.values
    if 'user_id' in session:
        g.user = session['user_id']

def after_request(response):
    response.request = request
    for f in registry:
        response = f(response)
    return response

def register(f):
    registry.append(f)
