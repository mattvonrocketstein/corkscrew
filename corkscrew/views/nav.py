''' corkscrew.views.nav
'''

from uuid import uuid4
import demjson

from .base import View
DEFAULT_MENU = [
    ['no menu data', [
        ['was posted','#'] ]
    ]]
class MenuError(Exception): pass

class MakeMenu(View):
    url = '/_make_menu'
    menu = None
    template = 'base_ajax.html'
    methods = 'get post'.split()
    def _check_menu(self, menu):
        for sub_title, submenu in menu:
            for item in submenu:
                if not isinstance(item, (tuple,list)):
                    raise MenuError(
                        'expected item from submenu {0}'.format(
                            submenu)+' would be a tuple or list,'
                        ' got {0}'.format(type(item)))


                if not len(item)==2:
                    raise MenuError(
                        'expected submenu item '
                        'would consist of href/link-name, '
                        'got '+str(item)+' instead')

    def get_menu(self):
        menu = self['menu']
        if isinstance(menu, basestring):
            menu = demjson.decode(menu)
        if menu is None:
            menu = self.menu or DEFAULT_MENU
        self._check_menu(menu)
        return menu

    def main(self):
        '''{{out|safe}}'''
        menu = self.get_menu()
        uuid = self['menu_id'] or str(uuid4()).replace('-','_')
        out = '<div id=menu_{uuid} ><ul class="dropdown">'
        for i in range(len(menu)):
            menu_header, submenu = menu[i]
            simple_link = isinstance(submenu, basestring)
            if simple_link: target = submenu
            else: target='#'
            tmp = "<li><a href={href}>{hdr}</a>"
            if simple_link:
                tmp+='</li>'
            tmp = tmp.format(hdr=menu_header, href=target)
            if not simple_link and submenu:
                tmp += '<ul class="sub_menu">'
                for item in submenu:
                    name, href = item
                    tmp += '<li><a href={href}>{name}</a></li>'.format(
                        href=href, name=name) + '</li>'
                tmp+='</ul>'
            tmp += '</li>'
            out += tmp
        out = out.format(uuid=uuid)+'</ul></div>'
        return self.render(
            body=out,
            extra_scripts = [
                '/static/js/menu/jquery.dropdownPlain.js',
                '/static/js/jquery.min.js',],
            extra_css = [
            '/static/js/menu/style.css'],)


class Nav(View):
    url = '/_nav'
    template = 'navigation.html'
    methods = 'get post'.split()

    def main(self):
        return self.render()
