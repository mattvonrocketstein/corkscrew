""" hammock.views.db
"""

from flask import render_template

from corkscrew import View
from corkscrew.blueprint import BluePrint
from report import report as report

from corkscrew.hammock.utils import memoized_property
from .tags import TagMixin

class DBView(View):
    """ abstract view for helping with access to a particular database """

    database_name  = None
    db_schema      = None

    def __init__(self, *args, **kargs):
        super(DBView, self).__init__(*args, **kargs)
        assert self.db_schema, 'expected db schema for {0}'.format(self)
        self.db_schema.view = self
        ## DOC
        if getattr(self, 'Tags', False):
            self._setup_tags(*args, **kargs)

    def _setup_tags(self, *args, **kargs):
        if isinstance(self.Tags, TagMixin):
            raise Exception, 'already initialized'
        report('installing tagging')
        clsname = 'DynTags{0}'.format(self.__class__.__name__)
        self.Tags = type(clsname,
                         (DBView, self.Tags, TagMixin),
                         dict(blueprint=BluePrint(clsname),
                              db_schema = self.db_schema,
                              database_name = self.database_name,
                              parent_url=self.url,
                              methods = ['GET', 'POST'],
                              url=self.url+'/tags'))
        self.Tags = self.Tags(*args, **kargs)

    def install_into_app(self, app):
        out = super(DBView,self).install_into_app(app)
        if hasattr(self, 'Tags'):
            out += [self.Tags]
        return out

    def build_new_entry(self):
        """ not really quite generic enough.
            still it depends on 'stamp' as pk
        """
        entry = self.db_schema()   # as dictionary
        entry.save()
        return entry

    def schema(self):
        """ returns a new, empty entry for the books database
        """
        if self.db_schema is None:
            err = 'subclasses should override db_schema first..'
            raise TypeError(err)
        tmp = self.db_schema()
        return tmp

    @memoized_property
    def _db(self):
        """ not sure yet whether caching this is safe.  we shall see """
        return self.server[self.database_name]

    @property
    def rows(self):
        if self['tag']:
            keys = self.filter_where_tag_is(self['tag'])
            queryset = (self._db[x] for x in keys)
            for row in queryset:
                yield row.id, dict(row)

        else:
            queryset = self._db.all()
            for row in queryset:
                yield row.id, row.value

    def rows_at(self, attr_name):
        """ DEPRECATE """
        q = '''function(doc){emit(null, doc.%s);}''' % attr_name
        out = [ x.value for x in self._db.query(q) ]
        return out

    def _all_unique_tags(self):
        return self.db_schema.objects.distinct('tags')

    def get_entry(self, _id):
        return self.db_schema.objects.get(id=_id)

    #@memoized_property
    #def server(self): return Server()

    def _tag_filter_function(self, tag):
        """ TODO: dryer"""
        out = render_template('js/tag_query.js', tag=tag)
        print '-'*70, out, '-'*70
        return out

    def filter_where_tag_is(self, tag):
        """ NOTE: returns keys only! """
        q = self._tag_filter_function(tag)
        return [ x.id for x in self._db.query(q) ]
