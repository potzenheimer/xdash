# -*- coding: utf-8 -*-
"""Module providing google analytics api access"""
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

    def get_results(context):
        """ Get results form ga api

        :param service: Apiclient service authorized via oauth2client
            credentials. The service object can be initialized once per session
            and passed to each subsequent query.
        :type service: service object

        :param profile_id: Id of the api profile to query
        :type profile_id: string

        :param query_type: Type of query passed as medium name, e.g. referral
            or organic search sources
        :type query_type: string
        """


class GATool(grok.GlobalUtility):
    grok.provides(IGATool)

    def get(self, **kwargs):
        if 'service' in kwargs:
            service = kwargs['service']
        else:
            service = self.initialize_service()
        try:
            if 'qt' in kwargs:
                qt = kwargs['qt']
                # return self._get_data(service, kwargs['qt'], kwargs['id'])
                if qt == 'accounts':
                    query = service.management().accounts().list()
                if qt == 'properties':
                    query = service.management().webproperties().list(
                        accountId=kwargs['account_id'])
                if qt == 'profiles':
                    query = service.management().profiles().list(
                        accountId=kwargs['account_id'],
                        webPropertyId=kwargs['property_id'])
                return query.execute()
            else:
                return self.get_results(service,
                                        kwargs['profile_id'],
                                        kwargs.get('query_type', None))
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

    def get_results(self, service, profile_id, query_type=None):
        timerange = self.get_month_timerange()
        start = timerange['first'].strftime('%Y-%m-%d')
        end = timerange['last'].strftime('%Y-%m-%d')
        if query_type is None:
            query = service.data().ga().get(
                ids='ga:' + profile_id,
                # start_date=start,
                start_date='2013-01-01',
                end_date=end,
                metrics=','.join(self.report_metrics()),
                prettyPrint=True,
                output='dataTable'
            )
        if query_type is 'keywords':
            query = service.data().ga().get(
                ids='ga:' + profile_id,
                # start_date=start,
                start_date='2013-01-01',
                end_date=end,
                dimensions='ga:keyword',
                sort='-ga:sessions',
                metrics=','.join(self.report_metrics_base()),
                # filters='ga:medium==${0}'.format(query_type),
                prettyPrint=True,
                output='dataTable',
                max_results='20'
            )
        else:
            query = service.data().ga().get(
                ids='ga:' + profile_id,
                # start_date=start,
                start_date='2013-01-01',
                end_date=end,
                dimensions='ga:source',
                sort='-ga:pageviews',
                metrics=','.join(self.report_metrics_base()),
                filters='ga:medium==${0}'.format(query_type),
                prettyPrint=True,
                # output='dataTable'
            )
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
        last = first_current - datetime.timedelta(days=1)
        info['first'] = datetime.datetime(last.year, last.month, 1)
        info['last'] = last
        return info

    def report_metrics_base(self):
        # besuche, pageviews, besuchsdauer, neue besuche, absprungrate
        metrics = (
            u'ga:sessions',
            u'ga:pageviews',
            u'ga:pageviewsPerSession',
            u'ga:sessionDuration',
            u'ga:percentNewSessions',
            u'ga:exitRate'
        )
        return metrics

    def report_metrics(self):
        metrics = (
            u'ga:sessions',
            u'ga:bounces',
            u'ga:sessionDuration',
            u'ga:pageviews',
            u'ga:hits',
            u'ga:organicSearches',
            u'ga:percentNewSessions',
            u'ga:pageviewsPerSession',
            u'ga:avgTimeOnPage',
            u'ga:exitRate'
        )
        return metrics
