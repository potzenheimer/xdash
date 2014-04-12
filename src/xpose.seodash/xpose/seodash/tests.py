import doctest
import unittest

from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.layer import onsetup

import xpose.seodash

OPTION_FLAGS = doctest.NORMALIZE_WHITESPACE | \
               doctest.ELLIPSIS

ptc.setupPloneSite(products=['xpose.seodash'])


class TestCase(ptc.PloneTestCase):

    class layer(PloneSite):

        @classmethod
        def setUp(cls):
            zcml.load_config('configure.zcml',
              xpose.seodash)

        @classmethod
        def tearDown(cls):
            pass


def test_suite():
    return unittest.TestSuite([

        # Unit tests
        #doctestunit.DocFileSuite(
        #    'README.txt', package='xpose.seodash',
        #    setUp=testing.setUp, tearDown=testing.tearDown),

        #doctestunit.DocTestSuite(
        #    module='xpose.seodash.mymodule',
        #    setUp=testing.setUp, tearDown=testing.tearDown),


        # Integration tests that use PloneTestCase
        ztc.ZopeDocFileSuite(
            'INTEGRATION.txt',
            package='xpose.seodash',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),

        # -*- extra stuff goes here -*-

        # Integration tests for Report
        ztc.ZopeDocFileSuite(
            'Report.txt',
            package='xpose.seodash',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for Project
        ztc.ZopeDocFileSuite(
            'Project.txt',
            package='xpose.seodash',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for Dashboard
        ztc.ZopeDocFileSuite(
            'Dashboard.txt',
            package='xpose.seodash',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        # Integration tests for DashboardFolder
        ztc.ZopeDocFileSuite(
            'DashboardFolder.txt',
            package='xpose.seodash',
            optionflags = OPTION_FLAGS,
            test_class=TestCase),


        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
