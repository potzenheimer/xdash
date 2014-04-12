import doctest
import unittest

from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.layer import onsetup

import xpose.seotool

OPTION_FLAGS = doctest.NORMALIZE_WHITESPACE | \
               doctest.ELLIPSIS

ptc.setupPloneSite(products=['xpose.seotool'])


class TestCase(ptc.PloneTestCase):

    class layer(PloneSite):

        @classmethod
        def setUp(cls):
            zcml.load_config('configure.zcml',
              xpose.seotool)

        @classmethod
        def tearDown(cls):
            pass


def test_suite():
    return unittest.TestSuite([

        # Unit tests
        #doctestunit.DocFileSuite(
        #    'README.txt', package='xpose.seotool',
        #    setUp=testing.setUp, tearDown=testing.tearDown),

        #doctestunit.DocTestSuite(
        #    module='xpose.seotool.mymodule',
        #    setUp=testing.setUp, tearDown=testing.tearDown),


        # Integration tests that use PloneTestCase
        ztc.ZopeDocFileSuite(
            'INTEGRATION.txt',
            package='xpose.seotool',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),

        # -*- extra stuff goes here -*-

        # Integration tests for SeoTool
        ztc.ZopeDocFileSuite(
            'SeoTool.txt',
            package='xpose.seotool',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for Dashboard
        ztc.ZopeDocFileSuite(
            'Dashboard.txt',
            package='xpose.seotool',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for DashboardFolder
        ztc.ZopeDocFileSuite(
            'DashboardFolder.txt',
            package='xpose.seotool',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
