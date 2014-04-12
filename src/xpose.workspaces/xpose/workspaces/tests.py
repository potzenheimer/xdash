import doctest
import unittest

from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.layer import onsetup

import xpose.workspaces

OPTION_FLAGS = doctest.NORMALIZE_WHITESPACE | \
               doctest.ELLIPSIS

ptc.setupPloneSite(products=['xpose.workspaces'])


class TestCase(ptc.PloneTestCase):

    class layer(PloneSite):

        @classmethod
        def setUp(cls):
            zcml.load_config('configure.zcml',
              xpose.workspaces)

        @classmethod
        def tearDown(cls):
            pass


def test_suite():
    return unittest.TestSuite([

        # Unit tests
        #doctestunit.DocFileSuite(
        #    'README.txt', package='xpose.workspaces',
        #    setUp=testing.setUp, tearDown=testing.tearDown),

        #doctestunit.DocTestSuite(
        #    module='xpose.workspaces.mymodule',
        #    setUp=testing.setUp, tearDown=testing.tearDown),


        # Integration tests that use PloneTestCase
        ztc.ZopeDocFileSuite(
            'INTEGRATION.txt',
            package='xpose.workspaces',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),

        # -*- extra stuff goes here -*-

        # Integration tests for Dashboard
        ztc.ZopeDocFileSuite(
            'Dashboard.txt',
            package='xpose.workspaces',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for XeoFolder
        ztc.ZopeDocFileSuite(
            'XeoFolder.txt',
            package='xpose.workspaces',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for Workspace
        ztc.ZopeDocFileSuite(
            'Workspace.txt',
            package='xpose.workspaces',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
