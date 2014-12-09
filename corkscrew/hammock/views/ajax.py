""" hammock.views.ajax

    Factory for ajax attribute-setters
"""
import urlparse
import traceback
from flask import request

from report import report as report

from .db import DBView
from corkscrew.blueprint import BluePrint

class Setter(DBView):
    """
    """
    requires_auth = True
    returns_json  = True

    def main(self):
        """ ajax -- sets an attribute for a location

            flask does something weird so that this closure doesn't
            work the way it ought to.  hence we have to calculate 'attr'
            based on request path :(
        """
        try:
            this_attr = urlparse.urlsplit(request.url).path.split('_')[-1]
            _id   = self['id']
            obj = self.db_schema.objects.get(id=_id)
            msg = "in inner set for attribute {A} on obj {I} with value {V}"
            report(msg.format(I=obj,
                              A=this_attr,
                              V=request.form.keys()))

            val = request.args.get(this_attr)
            # 'or' needed because we don't want to set
            # it as None if the ajax screws up
            val = val or str(val)
            report("in inner set with", [val])
            obj = self.schema.objects.get(id=_id)
            if this_attr not in obj._fields:
                raise Exception("unknown field: "+this_attr)
            field  = obj._fields[this_attr]
            before = getattr(obj, field.name)
            error  = self._do_set(obj, field, val)
            after = getattr(obj, field.name)
            if not error:
                obj.save()
                report("changed from {0} to {1}".format(
                    before,after))
                return dict(result='ok')
            else:
                return dict(error=str(error))
        except Exception, e:
            # tornado ate my exception?
            traceback.print_exc(e)
            self.flash(str(e))
            return dict(error=str(e))

    def _do_set(self, obj, field, value):
        fname = field.name
        setattr(obj, fname, value)

class ListAppender(Setter):
    def _do_set(self, obj, field, value):
        from mongoengine.fields import ListField
        assert isinstance(field, ListField),"Should be list field"
        value = getattr(obj, field.name)+[value]
        setattr(obj, field.name, value)


def set_factory(database_name, attr, schema=None):
    """ """
    assert schema is not None, database_name
    name  = 'set_' + attr
    bases = (Setter,)
    dct   = dict(url  = '/set_' + attr,
                 attr = attr,
                 blueprint = BluePrint(database_name+'__'+name),
                 schema=schema,
                 db_schema=schema, #HACK
                 database_name=database_name)
    return type(name, bases, dct)

def append_factory(database_name, attr, schema=None):
    """ """
    assert schema is not None, database_name
    name  = 'append_' + attr
    bases = (ListAppender,)
    dct   = dict(url  = '/append_' + attr,
                 attr = attr,
                 blueprint = BluePrint(database_name+'__'+name),
                 schema=schema,
                 db_schema=schema, #HACK
                 database_name=database_name)
    return type(name, bases, dct)
