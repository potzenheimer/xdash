import json
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
from apiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.client import AccessTokenRefreshError

from xpose.seotool import MessageFactory as _

DEFAULT_SERVICE_TIMEOUT = socket.getdefaulttimeout()


class IGATool(Interface):
    """ API call processing and session data storage """


class GATool(grok.GlobalUtility):
    grok.provides(IGATool)

    def get(self, **kwargs):
        service = self.initialize_service()
        try:
            accounts = service.management().accounts().list().execute()
            results = []
            if accounts.get('items'):
                results = accounts.get('items')
                if 'account_id' in kwargs:
                    account_id = kwargs['account_id']
                    results = self.get_webproperties(service, account_id)
                elif 'property_id' in kwargs:
                    account_id = kwargs['account_id']
                    property_id = kwargs['property_id']
                    results = self.get_profiles(service,
                                                account_id,
                                                property_id)
                elif 'profile_id' in kwargs:
                    profile = kwargs['profile_id']
                    results = self.get_results(service, profile)
                else:
                    results = accounts.get('items')
            return results
        except TypeError as error:
            # Handle errors in constructing a query.
            return 'There was an error constructing your query : {0}'.format(
                error)
        except HttpError as error:
            # Handle API errors.
            return ('Arg, there was an API error : {0} : {1}'.format(
                error.resp.status, error._get_reason()))
        except AccessTokenRefreshError:
            msg = _(u"The credentials have been revoked or expired,"
                    u"please re-run the application to re-authorize")
            return {'status': _(u"Error"),
                    'msg': msg}

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

    def initialize_service(self):
        service_url = self.get_config('api_uri')
        # client_email = self.get_config('client_email')
        keyfile = self.get_keyfile()
        record_key = 'xeo.cxn.ga_client_secret'
        record = api.portal.get_registry_record(record_key)
        gas = json.loads(record)
        access_data = gas['web']
        credentials = SignedJwtAssertionCredentials(
            access_data['client_email'],
            keyfile,
            scope=service_url)
        http = credentials.authorize(httplib2.Http())
        service = build('analytics', 'v3', http=http)
        return service

    def get_webproperties(self, service, account_id):
        query = service.management().webproperties().list(
            accountId=account_id)
        feed = query.execute()
        return feed

    def get_profiles(self, service, account_id, property_id):
        query = service.management().profiles().list(
            accountId=account_id,
            webPropertyId=property_id)
        feed = query.execute()
        return feed

    def get_results(self, service, profile_id):
        query = service.data().ga().get(
            ids='ga:' + profile_id,
            start_date='2012-03-03',
            end_date='2012-03-03',
            metrics='ga:sessions')
        feed = query.execute()
        return feed

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
                                'ga-pk.p12')
        return open(p12_file).read()

    def get_month_timerange(self):
        today = datetime.datetime.today()
        info = {}
        first_current = datetime.datetime(today.year, today.month, 1)
        last = first_current - datetime.datime.timedelta(days=1)
        info['first'] = datetime.datetime(last.year, last.month, 1)
        info['last'] = last
        return info
