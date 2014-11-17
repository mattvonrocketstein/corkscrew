""" corkscrew.bin._corkscrew
"""
def entry(settings=None):
    """ Main entry point """
    from corkscrew import settings
    settings = settings.Settings()
    settings.run()

if __name__=='__main__':
    entry()
