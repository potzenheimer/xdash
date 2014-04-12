import os
import socket
import requests
import contextlib
import httplib2
import datetime
from five import grok
from plone import api
from zope.interface import Interface
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

DEFAULT_SERVICE_TIMEOUT = socket.getdefaulttimeout()


class IGATool(Interface):
    """ API call processing and session data storage """


class GATool(grok.GlobalUtility):
    grok.provides(IGATool)

    def get(self, **kwargs):
        service_url = self.get_config('api_uri')
        client_email = self.get_config('client_email')
        keyfile = self.get_keyfile()
        credentials = SignedJwtAssertionCredentials(
            client_email,
            keyfile,
            scope=service_url)
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build('analytics', 'v3', http=http)
        # params = urlencode(sorted(kwargs.iteritems()))
        accounts = service.management().accounts().list().execute()
        import pdb; pdb.set_trace( )
        data_query = service.data().ga().get(**{
            'ids': 'ga:YOUR_PROFILE_ID_NOT_UA',
            'metrics': 'ga:visitors',
            'start_date': '2013-01-01',
            'end_date': '2015-01-01'
        })
        feed = data_query.execute()
        return feed['rows'][0][0]

    def status(self):
        info = {}
        info['name'] = 'GA'
        service_url = self.get_config('api_uri')
        url = service_url
        with contextlib.closing(requests.get(url, verify=False)) as response:
            r = response
        if r.status_code == requests.codes.ok:
            info['code'] = 'active'
        else:
            info['code'] = 'unreachable endpoint'
        return info

    def get_analytics_visitors():
        f = open('ga-privatekey.p12', 'rb')
        key = f.read()
        f.close()
        credentials = SignedJwtAssertionCredentials(
            'xxx@developer.gserviceaccount.com',
            key,
            scope='https://www.googleapis.com/auth/analytics.readonly')
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build('analytics', 'v3', http=http)
        data_query = service.data().ga().get(**{
            'ids': 'ga:YOUR_PROFILE_ID_NOT_UA',
            'metrics': 'ga:visitors',
            'start_date': '2013-01-01',
            'end_date': '2015-01-01'
        })
        feed = data_query.execute()
        return feed['rows'][0][0]

    def get_config(self, record=None):
        record_key = 'xeo.cxn.google_{0}'.format(record)
        record = api.portal.get_registry_record(record_key)
        return record

    def get_keyfile(self):
        p12_file = os.path.join(os.path.dirname(__file__),
                                'ga-privatekey.p12')
        return open(p12_file).read()

    def get_month_timerange(self):
        today = datetime.datetime.today()
        info = {}
        first_current = datetime.datetime(today.year, today.month, 1)
        last = first_current - datetime.datime.timedelta(days=1)
        info['first'] = datetime.datetime(last.year, last.month, 1)
        info['last'] = last
        return info
