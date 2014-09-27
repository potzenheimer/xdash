# -*- coding: utf-8 -*-
"""Module processing data collection for reports"""

import json
import time
from Acquisition import aq_inner
from five import grok
from plone import api

from plone.keyring import django_random
from zope.component import getUtility
from zope.lifecycleevent import modified

from plone.app.contentlisting.interfaces import IContentListing

from xpose.seodash.dashboardfolder import IDashboardFolder
from xpose.seodash.dashboard import IDashboard
from xpose.seodash.report import IReport


class DataCollector(grok.View):
    grok.context(IDashboardFolder)
    grok.require('zope2.View')
    grok.name('data-collector')

    def render(self):
        context = aq_inner(self.context)
        if len(self.dashboards()) > 0:
            reports = self._collect()
        next_url = context.absolute_url()
        return self.request.response.redirect(next_url + '?created=' + reports)

    def dashboards(self):
        context = aq_inner(self.context)
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        path=dict(query='/'.join(context.getPhysicalPath()),
                                  depth=1))
        return IContentListing(items)

    def _collect(self):
        idx = 0
        dashboards = self.dashboards()
        for board in dashboards:
            projects = getattr(board, 'projects')
            if len(projects):
                for p in projects:
                    report = self._create_report()
                    setattr(report, 'projectId', p['id'])
                    metrics = {
                        'dashboard': api.content.get_uuid(obj=board),
                        'projectId': p['id'],
                        'created': '',
                        'updated': '',
                        'metrics': list()
                    }

                    setattr(report, 'report', json.dumbs(metrics))
                modified(board)
                board.reindexObject(idxs='modified')
        return idx

    def _create_report(self):
        context = aq_inner(self.context)
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xpose.seodash.report',
            id=token,
            title='report-{0}'.format(token),
            container=context,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        return uuid

    def _build_report_xovi(self):
        context = aq_inner(self.context)
        report = {}
        stored_report = getattr(context, 'report_xovi', None)
        if stored_report:
            report = json.loads(stored_report)
        tool = getUtility(IXoviTool)
        status = tool.status()
        if status['code'] == 'active':
            ses = tool.get(
                service=u'seo',
                method=u'getSearchEngines',
            )
            report['getSearchengines'] = ses
            kws = tool.get(
                service=u'seo',
                method=u'getKeywords',
                sengine=u'google.de',
                domain=u'xpose414.de',
            )
            report['getKeywords'] = kws
            daily_kws = tool.get(
                service=u'seo',
                method=u'getDailyKeywords',
            )
            report['getDailyKeywords'] = daily_kws
            lost_kws = tool.get(
                service=u'seo',
                method=u'getLostKeywords',
                sengineid=u'1',
                domain=u'xpose414.de',
            )
            report['getLostKeywords'] = lost_kws
        return report


class ReportDataCollector(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('report-data-collector')

    """ Collect data from external apis and return the report for storage
    """

    def update(self, *args, **kwargs):
        grok.View.update(self, *args, **kwargs)

    def collect(self, uid=None, ga_service=None):
        state = 'pending'
        if uid is not None:
            state = 'success'
        return state

    def _process_request(self):
        context = aq_inner(self.context)
        stored_report = getattr(context, 'report', None)
        report = json.loads(stored_report)
        metrics = report['items']
        # Build report metrics here
        import pdb; pdb.set_trace()
        return report

    def render(self, *args, **kwargs):
        start = time.time()
        data = self._process_request()
        end = time.time()
        data.update(dict(_runtime=end-start))
        self.request.response.setHeader("Content-Type", "application/json")
        return json.dumps(data)
