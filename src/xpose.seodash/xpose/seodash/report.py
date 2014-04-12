import json
from datetime import datetime
from Acquisition import aq_inner
from five import grok
from plone import api
from zope.component import getUtility

from z3c.form import group, field
from zope import schema
from zope.lifecycleevent import modified
from zope.interface import invariant, Invalid
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.dexterity.content import Container

from plone.directives import dexterity, form
from plone.app.textfield import RichText
from plone.namedfile.field import NamedImage, NamedFile
from plone.namedfile.field import NamedBlobImage, NamedBlobFile
from plone.namedfile.interfaces import IImageScaleTraversable

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder

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
        required=True,
    )
    domain = schema.TextLine(
        title=_(u"Site URI / Domainname"),
        required=True,
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


class Report(Container):
    grok.implements(IReport)

    # Add your class methods and properties here
    pass


class View(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('view')

    def tracking_report(self):
        context = aq_inner(self.context)
        return context.restrictedTraverse('@@report-tracking')()

    def filter_tracking(self):
        context = aq_inner(self.context)
        metrics = getattr(context, 'report_ac')
        timeframe = datetime.datetime.utcnow().replace(day=1) - datetime.timedelta(days=1)
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
        context = aq_inner(self.context)
        metrics = getattr(context, 'report_ac')
        timeframe = datetime.datetime.utcnow().replace(day=1) - datetime.timedelta(days=1)
        data = {}
        return data


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
        self.clean_ac_record()
        return self.request.response.redirect(next_url)

    def clean_ac_record(self):
        context = aq_inner(self.context)
        data = getattr(context, 'report_ac')
        as_json = json.dumps(data)
        setattr(context, 'report_ac', as_json)
        modified(context)
        return as_json

    def _build_report_ga(self):
        context = aq_inner(self.context)
        tool = getUtility(IGATool)
        data = tool.get()
        return data

    def _build_report_ac(self):
        context = aq_inner(self.context)
        project_id = '2'
        pinfo = u'projects/{0}/tracking'.format(project_id)
        tool = getUtility(IACTool)
        data = tool.make_request(path_info=pinfo)
        setattr(context, 'report_ac', data)
        modified(context)
        context.reindexObject(idxs='modified')
        return data

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
        setattr(context, 'report_xovi', data)
        modified(context)
        context.reindexObject(idxs='modified')
        return report
