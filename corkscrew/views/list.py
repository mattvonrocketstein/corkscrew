""" corkscrew.views.list
"""
class ListView(object):

    def get_ctx(self):
        ctx = super(ListView, self).get_ctx()
        tmp = self.db_schema.objects.all()
        if getattr(self,'Tags',False): #hack
            if self['tag']:
                tmp = tmp.filter(tags__in=[self['tag']])
            if self['author']:
                # TODO: proximate matches via hamming distance or solr
                tmp = tmp.filter(author=self['author'])
            ctx.update(tags = self.Tags._all_unique_tags())
        ctx.update(
            this_url=self.url,
            item_list=tmp)
        return ctx

    def list(self):
        return self.render_template(**self.get_ctx())

    def main(self):
        if self.authorized and self['id']:
            # must mixin editable
            return self.edit()
        if self['detail']:
            return self.detail()
        if self['remove']:
            # Must mixin removable
            return self.remove()
        else:
            return self.list()
