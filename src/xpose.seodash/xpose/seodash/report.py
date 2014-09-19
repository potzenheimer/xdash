# -*- coding: utf-8 -*-
"""Module providing report content type setup and funcitonality"""
import json
from Acquisition import aq_inner
from Acquisition import aq_parent
from five import grok
from zope import schema
from plone import api

from plone.indexer import indexer
from zope.component import getUtility
from zope.lifecycleevent import modified

from plone.dexterity.content import Container

from plone.directives import form
from plone.namedfile.interfaces import IImageScaleTraversable

from xpose.seotool.ac import IACTool
from xpose.seotool.ga import IGATool
from xpose.seotool.xovi import IXoviTool


from xpose.seodash import MessageFactory as _


# Interface class; used to define content-type schema.

class IReport(form.Schema, IImageScaleTraversable):
    """
    A collection of metrics and dimensions
    """
    site = schema.URI(
        title=_(u"Site URI"),
        required=False,
    )
    domain = schema.TextLine(
        title=_(u"Site URI / Domainname"),
        required=False,
    )
    projectId = schema.TextLine(
        title=_(u"Project ID"),
        required=False,
    )
    report = schema.TextLine(
        title=_(u"Xovi Report"),
        description=_(u"Automatically updated report consisting of predefined "
                      u"methods and values"),
        required=False,
    )
    report_xovi = schema.TextLine(
        title=_(u"Xovi Report"),
        description=_(u"Automatically updated report consisting of predefined "
                      u"methods and values"),
        required=False,
    )
    report_ac = schema.TextLine(
        title=_(u"Xovi Report"),
        description=_(u"Automatically updated report consisting of predefined "
                      u"methods and values"),
        required=False,
    )
    report_ga = schema.TextLine(
        title=_(u"Xovi Report"),
        description=_(u"Automatically updated report consisting of predefined "
                      u"methods and values"),
        required=False,
    )


@indexer(IReport)
def projectIndexer(obj):
    return obj.projectId
grok.global_adapter(projectIndexer, name="projectId")


class Report(Container):
    grok.implements(IReport)

    # Add your class methods and properties here
    pass


class View(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('view')

    def report(self):
        context = aq_inner(self.context)
        report = getattr(context, 'report', None)
        data = dict()
        if report is not None:
            data = json.loads(report)
        return data

    def tracking_report(self):
        context = aq_inner(self.context)
        return context.restrictedTraverse('@@report-tracking')()

    def project_info(self):
        context = aq_inner(self.context)
        parent = aq_parent(context)
        from xpose.seodash.dashboard import IDashboard
        if IDashboard.providedBy(parent):
            container = parent
        else:
            container = aq_parent(parent)
        return getattr(container, 'projects')

    def build_report_ga(self):
        tool = getUtility(IGATool)
        projects = self.project_info()
        project = projects[0]
        pid = project['ga']
        # data = tool.get(profile_id=pid, query_type='keywords')
        data = tool.get(profile_id=pid, query_type='referral')
        return data

    def print_report(self):
        data = self.build_report_ga()
        return data

    def filter_tracking(self):
        # context = aq_inner(self.context)
        # metrics = getattr(context, 'report_ac')
        # timeframe = (datetime.datetime.utcnow().replace(day=1) -
        #     datetime.timedelta(days=1))
        data = {}
        return data


class ContentView(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('content-view')

    def tracking_report(self):
        context = aq_inner(self.context)
        return context.restrictedTraverse('@@report-tracking')()

    def filter_tracking(self):
        # context = aq_inner(self.context)
        # metrics = getattr(context, 'report_ac')
        # timeframe = (datetime.datetime.utcnow().replace(day=1) -
        #    datetime.timedelta(days=1))
        data = {}
        return data


class LinkBuilding(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('report-linkbuilding')

    def report(self):
        context = aq_inner(self.context)
        data = getattr(context, 'report')
        report = json.loads(data)
        return report


class Tracking(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('report-tracking')

    def metrics(self):
        context = aq_inner(self.context)
        data = getattr(context, 'report_ac')
        report = json.loads(data)
        return report[:10]


class RequestReport(grok.View):
    grok.context(IReport)
    grok.require('cmf.ManagePortal')
    grok.name('build-report')

    def render(self):
        context = aq_inner(self.context)
        next_url = context.absolute_url()
        self.ga_record()
        return self.request.response.redirect(next_url)

    def project_info(self):
        context = aq_inner(self.context)
        parent = aq_parent(context)
        from xpose.seodash.dashboard import IDashboard
        if IDashboard.providedBy(parent):
            container = parent
        else:
            container = aq_parent(parent)
        return getattr(container, 'projects')

    def report(self):
        context = aq_inner(self.context)
        data = []
        stored_report = getattr(context, 'report', None)
        if stored_report is not None:
            report = json.loads(stored_report)
            metrics = report['items']
        return metrics

    def _build_report_ac(self):
        context = aq_inner(self.context)
        projects = self.project_info()
        project = projects[0]
        project_id = project['ac']
        pinfo = u'projects/{0}/tracking'.format(project_id)
        tool = getUtility(IACTool)
        data = tool.make_request(path_info=pinfo)
        as_json = json.dumps(data)
        setattr(context, 'report_ac', as_json)
        modified(context)
        context.reindexObject(idxs='modified')
        return data

    def postprocess_ac_record(self):
        context = aq_inner(self.context)
        report = self.report()
        ac_data = getattr(context, 'report_ac')
        ac_report = json.loads(ac_data)
        metric = report[1]
        table = metric['dataTable']
        rows = table['rows']
        for entry in ac_report[:50]:
            time_rec = entry['record_date']['mysql']
            time_comps = time_rec.split('-')
            entry_date = '{0}.{1}.{2}'.format(time_comps[2],
                                              time_comps[1],
                                              time_comps[0])
            new_row = {
                'xd:trackingDate': entry_date,
                'xd:trackingUserId': entry['user']['display_name'],
                'xd:trackingSummary': entry['summary'],
                'xd:trackingValue': entry['value']
            }
            rows.append(new_row)
        table['rows'] = rows
        metric['dataTable'] = table
        stored = getattr(context, 'report')
        data = json.loads(stored)
        items = data['items']
        items[1] = metric
        setattr(context, 'report', json.dumps(data))
        modified(context)
        context.reindexObject(idxs='modified')
        msg = _(u"Built links data table was successfully updated")
        api.portal.show_message(msg, self.request)
        return msg

    def clean_ac_record(self):
        context = aq_inner(self.context)
        data = getattr(context, 'report_ac')
        as_json = json.dumps(data)
        setattr(context, 'report_ac', as_json)
        modified(context)
        return as_json

    def build_report_ga(self):
        tool = getUtility(IGATool)
        projects = self.project_info()
        project = projects[0]
        pid = project['ga']
        data = tool.get(profile_id=pid, query_type='keywords')
        return data

    def ga_record(self):
        context = aq_inner(self.context)
        report = self.report()
        ga_report = self.build_report_ga()
        metric = report[2]
        data_table = ga_report['dataTable']
        metric['dataTable'] = data_table
        stored = getattr(context, 'report')
        data = json.loads(stored)
        items = data['items']
        items[2] = metric
        setattr(context, 'report', json.dumps(data))
        modified(context)
        context.reindexObject(idxs='modified')
        msg = _(u"Built links data table was successfully updated")
        api.portal.show_message(msg, self.request)
        return msg

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
        data = json.dumps(report)
        setattr(context, 'report_xovi', json.dumps(data))
        modified(context)
        context.reindexObject(idxs='modified')
        return report
