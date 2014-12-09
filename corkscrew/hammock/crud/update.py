""" hammock/crud/update
"""

# TODO: not yet generic.. moved to robotninja.coords
#from .remove import Remove

#TODO: move to utilities
#from hammock.util import nomprivate_editable
import demjson
from collections import defaultdict

from mongoengine import ListField
from jinja2 import Template
from flask import render_template

from report import report

from corkscrew.hammock.utils import authorization_required

def nonprivate_editable(key, db_schema):
    """ """
    return not key.startswith('_') and key not in db_schema._no_edit

TYPE_MAP = defaultdict(lambda: 'widgets/string_type.html')
TYPE_MAP.update({ type('') : 'widgets/string_type.html',
                  type(u'') : 'widgets/string_type.html',
                  type(tuple()) : 'widgets/tuple_type.html',
                  type([]) : 'widgets/tuple_type.html',
                  type(None): 'widgets/none_type.html'
                  })

class Editable(object):
    """

    Mixin requires:

      edit_template::

      update_url::

      db_schema::

      redirect_success::
        where to redirect to on successful update.
        templates may choose not to use this.
    """

    def resolve_template_from_string(self, name):
        """ returns a triple of
            ( <string-src>,
              <abs-path-to-template>,
              <function uptodate(?)> )
        """
        assert name
        return self.app.jinja_loader.get_source(self.app.jinja_env, name)

    @authorization_required
    def edit(self):
        """ """
        # get or create a new entry id
        _id   = self['id']
        entry = self.build_new_entry() if _id=='new' else self.get_entry(_id)
        _id   = entry.id

        editable_parts = []

        #items = [ [key, val] for key, val in entry.to_json().items() \
        #          if nonprivate_editable(key, self.db_schema) ]
        items = entry._data.copy()
        items.pop('id')
        items = [ [k,v] for k,v in items.items() if nonprivate_editable(k, self.db_schema)]
        for key, val in items:
            # find overrides in request data
            for skey, sval in self.request.args.items():
                if skey==key:
                    val = sval
            widget = self._get_widget(key, value=val, schema=self.db_schema)
            editable_parts.append([key, widget])

        # find keys unexpected missing from request that are still in schema.
        # this allows updated schema's to still present correct information
        # in ajax update dialogs
        tmp = set(self.db_schema._fields.keys()) - \
              set(dict(items).keys()).union(set(self.db_schema._no_edit))
        for key in tmp:
            editable_parts.append(
                [key,
                 self._get_widget(key,
                                  value = self.db_schema._fields[key].default,
                                  schema=self.db_schema)])
        return render_template(self.edit_template,
                               update_url=self.update_url,
                               id=_id,
                               obj=editable_parts)
    def _get_widget(self, key, value=None, schema=None):
        template = self._get_template(key, value=value, schema=schema,)
        field = getattr(schema, key, None)
        if field is None:
            report('oops, could not get field for {0} from {1}'.format(key, schema))
        if isinstance(field, ListField):
            # get rid of u's for stuff like [u"foo",]
            value = demjson.encode(value)
        result = template.render(key=key, default="DEFAULT-IS-DEPRECATED",
                                 # because we dont want to have stuff like
                                 # value="["one"]" in the html
                                 value=unicode(value).replace('"', "'"))
        return result

    def _get_template(self, key, schema=None, value='no-value', loader=None):
        """ get a (blank) template for editing this key from the
            database schema, failing that return the default
        """
        from_schema_definition = schema._render.get(key, None)
        from_best_guess = TYPE_MAP[type(getattr(schema,key))]
        if from_schema_definition:
            out = from_schema_definition
        else:
            out = self.resolve_template_from_string(from_best_guess)[0]
        return Template(out)
