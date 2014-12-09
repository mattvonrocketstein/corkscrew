""" hammock.views.remove
"""

from flask import jsonify

from corkscrew.hammock.utils import authorization_required

from report import report

class Removable(object):
    """ mixin for item deletion """

    @authorization_required
    def remove(self):
        _id   = self['remove']
        report("Removing {id} from {db}", id=_id, db=self.db_schema)
        self.db_schema.objects.get(id=_id).delete()
        return jsonify(dict(ok='true'))
