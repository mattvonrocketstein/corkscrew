""" hammock.views.tags
"""
from jinja2 import Template
import json
from flask import render_template, jsonify
class TagMixin(object):
    """ FIXME: this now belongs in hammock """

    def _all_unique_tags(self):
        return self.db_schema.objects.distinct('tags')

    def tag_helper(self):
        """ eg /blog/tags?tag_helper=<id>
            render the gui for nice tag editing
        """
        if not self.authorized:
            return "You need to login."
        return render_template("tag_helper.html",
                               this_url=self.url,
                               tags=self.tags,
                               id=self['tag_helper'],
                               parent_url=self.parent_url)

    @property
    def tags(self):
        """ returns a sorted list of all the known tags for this database
        """
        tags = list(self._all_unique_tags())
        tags.sort()
        return tags

    def get(self):
        """ eg /blog/tags?id=....

            get tags for a db entry in json
        """
        key = self['id']
        entry = self.db_schema.objects.get(id=key)
        return jsonify(dict(tags=entry['tags']))

    def set(self):
        """ eg /blog/tags?set=<id>&tags=<tags>
        """
        if not self.authorized:
            return jsonify(dict(ok="false", error="unauthorized"))
        key = self['set']
        tags = json.loads(self['tags'])
        tags = [str(x['title']) for x in tags]
        entry = self.db_schema.objects.get(id=key)
        entry.tags=tags
        entry.save()
        return jsonify(dict(ok="true"))

    def main(self):
        """
        {%for t in tags%}
        <a href="{{parent_url}}?tag={{t}}">{{t}}</a> |
        {%endfor%}
        """
        #if self['_']:

        if self['tag_helper']:
            return self.tag_helper()
        elif self['id']:
            return self.get()
        elif self['set']:
            return self.set()
        else:
            template = self.Template(self.main.__doc__)
            return template.render(parent_url=self.parent_url,
                                   tags=self.tags)
TagMixin.Template = Template
