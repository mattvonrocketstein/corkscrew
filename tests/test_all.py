""" corkscrew/tests/test_all
"""
from unittest import TestCase

class TestPyPkg(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

    def test_2(self):
        pass

    def test_version(self):
        from corkscrew.version import __version__
        self.assertTrue(isinstance(__version__, float))

    def test_data(self):
        # maybe assert that there are no other modules
        # in the namespace? other than that there is not
        # much to do.  just make sure the import isn't broken
        from corkscrew.data import *
