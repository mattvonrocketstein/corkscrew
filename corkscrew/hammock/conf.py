""" hammock.conf
"""

from corkscrew import Settings as _Settings

class Settings(_Settings):
    """
    """
    default_file   = 'hammock.ini'
    backup_options = dict(dest='backup_database',
                          default='',
                          handler='doomwagon',
                          )
    extra_options  = ( ('--backup',), backup_options )

    def __init__(self,*args, **kargs):
        """
            ugh hack
        """
        super(Settings,self).__init__(*args, **kargs)
        from hammock import conf
        conf.settings = self

    def shell_namespace(self):
        """
        """
        dct = super(Settings,self).shell_namespace()
        return dct
