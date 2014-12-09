""" hammock._couch

    couchdb specific helpers.

    lots of this is pretty dumb, still need to figure out geocouch
"""
import base64
import itertools

import demjson
import couchdb
from peak.util.imports import lazyModule

from corkscrew.hammock.utils import AllStaticMethods
from report import report as report
from mongoengine import Document as mDocument
from mongoengine import ListField, StringField

from couchdb.client import Database as OriginalDatabase

def couchdb_pager(db, view_name='_all_docs', query=None,
                  startkey=None, startkey_docid=None,
                  endkey=None, endkey_docid=None, bulk=5000):
    """ stolen from:
    http://blog.marcus-brinkmann.de/2011/09/17/a-better-iterator-for-python-couchdb
    """
    # Request one extra row to resume the listing there later.
    options = {'limit': bulk + 1}
    if startkey:
        options['startkey'] = startkey
        if startkey_docid:
            options['startkey_docid'] = startkey_docid
    if endkey:
        options['endkey'] = endkey
        if endkey_docid:
            options['endkey_docid'] = endkey_docid
    done = False
    while not done:
        # query gets to override any mention of view
        if query is not None:
            view = db.query(query, **options)
        else:
            view = db.view(view_name, **options)
        rows = []
        # If we got a short result (< limit + 1), we know we are done.
        if len(view) <= bulk:
            done = True
            rows = view.rows
        else:
            # Otherwise, continue at the new start position.
            rows = view.rows[:-1]
            last = view.rows[-1]
            options['startkey'] = last.key
            options['startkey_docid'] = last.id

        for row in rows:
            yield row.id

class DatabaseMixin(object):
    """ """
    def _all_unique_attr(self, attrname):
        return [x.key for x in self.query(
            map_fun='''function(doc){emit(doc.%s, doc);}'''%attrname,
            reduce_fun="""function(keys, values){return true}""",
            group=True)]
    _unique_values_for_fieldname = _all_unique_attr

    def delete_all(self,really=False):
        if not really:
            report('seriously?  well ok, but pass `really=True`')
        else:
            for x in self:
                report('deleting: '+str(x))
                del self[x]

    def __mod__(self, q):
        """ for helping to paginate a defered query.
            use like this:
              db_keys = (database%query_javascript)[slice_start:slice_end]
        """
        report("running paged-query: ")
        report(
            report.highlight.javascript(q),
            plain=True)
        report.console.draw_line()
        pager = couchdb_pager(self, query=q)
        class DatabaseProxy(object):
            def __getitem__(himself, x):
                return self.__getitem__(x, pager=pager)
        return DatabaseProxy()

    def __getitem__(self, x, pager=None):
        """ the better to paginate with.
            use it like this:
              >>> database[key]   # works as usual
              >>> database[0:100] # returns 100 keys
        """
        if isinstance(x, slice):
            if pager is None:
                pager = couchdb_pager(self)
            return list(itertools.islice(pager,
                                         x.start,
                                         x.stop))
        else:
            return couchdb.client.Database.__getitem__(self, x)

    def _matching_values(self, field=None, value=None):
        return [ row for row in \
                 self.query("function(doc){emit(doc."+field+", doc)}",
                                key=value) ]
    def keys(self):
        return [k for k in self]

    def all(self):
        """ return iterator for all <Rows> """
        query = '''function(doc){ emit(doc._id, doc);} '''
        return (x for x in self.query(query))


class Server(couchdb.Server):
    """ """
    def __init__(self, conf=None):
        if conf is None:
            conf = lazyModule('hammock.conf')
        server = 'http://{0}:{1}/'.format(
            conf.settings['couch']['host'],
            conf.settings['couch']['port'])
        super(Server,self).__init__(server)
        self.resource.credentials = ( conf.settings['couch']['username'],
                                      base64.b64decode(conf.settings['couch']['password']) )

    def __getitem__(self, name):
        """ FIXME: just brutal.. """
        result = super(Server,self).__getitem__(name)
        result.__class__ = type('DynamicDatabase', (DatabaseMixin, result.__class__), {})
        return result

    def db_url(self, db_or_dbname):
        if isinstance(db_or_dbname, OriginalDatabase):
            dbname = db_or_dbname._name
        else:
            dbname = db_or_dbname
        return self.futon_url() + 'database.html?{0}'.format(dbname)

    def futon_url(self):
        url = self.resource.url
        if not url.endswith('/'): url+='/'
        return url + '_utils/'

    def document_url(self, db_name, doc_id):
        # http://localhost:5999/_utils/document.html?ixle_settings/ignore
        return "{0}document.html?{1}/{2}".format(
            self.futon_url(), db_name, doc_id)

    admin_url = db_url
    edit_url = db_url

def get_db(db_name):
    db_name = db_name
    return setup()[db_name]

def update_db(db, _id, dct, schema=None):
    """  stupid.. have to delete and restore instead of update? """

    if not schema:
        report('SCHEMA NOT PROVIDED!!!!!!!')
        report('updating db',[db, _id, dct])
        doc = db[_id]
        report('before',doc.items())

        for x in dct:
            doc[x] = dct[x]

        # TODO: use db.update(doc) ?
        #db[doc.id] = doc

        report('after', doc)
        report('updated "{id}" with new values for keys'.format(id=_id), dct.keys())
    else:
        doc = schema.load(db, _id)
        for x in dct:
            val = dct[x]
            fieldtype = getattr(schema, x).__class__
            if fieldtype==ListField:
                val = demjson.decode(val)
            elif fieldtype==StringField:
                pass
            else:
                raise Exception, 'NIY:'+str(fieldtype)
            setattr(doc, x, val)
        doc.store(db)
setup=Server

class Schema(object):
    """ _unpack:

         metadata that defines helper functions that take
         request-variables to values suitable for storage
         in the database.  for example, integers will come
         of requests as simple strings by default, to fix
         that use something like this the following

           >>> myschema._unpack['my_int_var'] = int
    """
    __metaclass__ = AllStaticMethods
    _unpack       = {}
    _render       = {}
    _no_edit      = []
    def save(self,db):
        return update_db(db, self.id, dict(self.items()), schema=self)

def unpack_as_schema(q, schema):
    """ unpack a request/dict into a dictionary according to this schema

        TODO: verification for multiple choice?
    """
    # because it might be a request
    q = q if isinstance(q,dict) else dict(q.values.items())
    assert issubclass(schema, mDocument), 'old style schema?'
    for var in q:
        field = getattr(schema, var, None)
        if field==None:
            # might be interval value e.g. '_rev', etc
            continue
        if isinstance(field, ListField) and not isinstance(q[var], list):
            q[var] = demjson.decode(q[var])
        #if isinstance(field, DateTimeField):
        #    q[var] = getattr(schema, var)._to_python( q[var] )
    return schema(**q)

class PersistentObject(object):
    """
    >>> APC = PersistentObject(db_name='pickles', property_name='airport_codes')

    """
    def __init__(self,db_name, property_name):
        self.db_name = db_name
        self.property_name = property_name

    @property
    def database(self):
        return Server()[self.db_name]

    @property
    def doc(self):
        pickles = self.database
        #try:
        apcs    = pickles[self.property_name]
        #except ResourceNotFound,e:
        #    apcs = dict(value=None)
        #    pickles[self.property_name] = apcs
        #    apcs    = pickles[self.property_name]
        return apcs

    def get(self):
        """ """
        return self.doc['value']

    def set(self,lst):
        doc = self.doc
        doc.update(value=lst)
        self.database[doc.id]=doc

    handle = property(get, set)
