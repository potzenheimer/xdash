import json
import socket
import contextlib
import requests
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
from five import grok
from plone import api
from zope.interface import Interface


DEFAULT_SERVICE_URI = 'https://api.xovi.net/index.php'
DEFAULT_SERVICE_TIMEOUT = socket.getdefaulttimeout()


class IXoviTool(Interface):
    """ API call processing and session data storage """

    def get(context):
        """ Get specific metrics

        @param timeout: Override api request timeout
        @param service: Service name or category e.g project
        @param method:  The specific method to retrieve
        @param domain:  Qualified domain name
        @param se:      Search engine to crawl
        """

    def status(context):
        """ Check availability of Xovi api

        @param timeout: Set status request timeout
        """

    def get_config(context):
        """ Get XOVI api records from configuration registry

        @param record: Specify desired record type e.g. client_key
        """


class XoviTool(grok.GlobalUtility):
    grok.provides(IXoviTool)

    def get(self, service=None, **kwargs):
        service_url = self.get_config('api_uri')
        service_key = self.get_config('client_key')
        params = xovi_request_base()
        params['service'] = service
        params['key'] = service_key
        additional_params = urlencode(sorted(kwargs.iteritems()))
        url = service_url + '?' + urlencode(params) + '&' + additional_params
        with contextlib.closing(requests.get(url, verify=False)) as response:
            r = response
            if r.status_code == requests.codes.ok:
                return r.json()

    def status(self):
        service_url = self.get_config('api_uri')
        service_key = self.get_config('client_key')
        params = xovi_request_base()
        info = {}
        info['name'] = 'XOVI'
        params['method'] = u'getCreditState'
        params['key'] = service_key
        url = service_url + '?' + urlencode(params)
        with contextlib.closing(requests.get(url, verify=False)) as response:
            r = response
        if r.status_code == requests.codes.ok:
            info['code'] = 'active'
        else:
            info['code'] = 'unreachable endpoint'
        return info

    def get_config(self, record=None):
        record_key = 'xeo.cxn.xovi_{0}'.format(record)
        record = api.portal.get_registry_record(record_key)
        return record


def xovi_request_base():
    parameters = {
        'service': u'user',
        'format':  u'json',
        'timeout': DEFAULT_SERVICE_TIMEOUT,
    }
    return parameters


def report_methods():
    methods = (
        u'getDailyKeywords',
        u'getLostKeywords',
        u'getKeywords'
    )
    return methods
