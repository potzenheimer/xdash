# -*- coding: utf-8 -*-
"""Module providing user dashboard content type and functionality"""

import datetime
import os
import time
import uuid as uuid_tool

from Acquisition import aq_inner
from five import grok
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.content import Container
from plone.directives import form
from plone.event.utils import pydt
from plone.keyring import django_random
from plone.namedfile.field import NamedBlobImage
from plone.namedfile.interfaces import IImageScaleTraversable
from string import Template
from zope import schema
from zope.lifecycleevent import modified

from xdash.boards.report import IReport

from xpose.seodash import MessageFactory as _


class IDashboard(form.Schema, IImageScaleTraversable):
    """
    A project dashboard
    """
    ga_id = schema.TextLine(
        title=_(u"GA Site ID"),
        required=False,
    )
    projects = schema.List(
        title=_(u"Dashboard settings"),
        description=_(u"Settings containing a project list"),
        value_type=schema.TextLine(
            title=_(u"Project"),
        ),
        required=False,
    )
    logo = NamedBlobImage(
        title=_(u"Logo Image"),
        description=_(u"Upload optional customer logo"),
        required=False,
    )


class Dashboard(Container):
    grok.implements(IDashboard)


class View(grok.View):
    grok.context(IDashboard)
    grok.require('zope2.View')
    grok.name('view')

    def update(self):
        self.has_reports = len(self.reports()) > 0

    def reports(self):
        context = aq_inner(self.context)
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IReport.__identifier__,
                        path=dict(query='/'.join(context.getPhysicalPath()),
                                  depth=2),
                        sort_on='modified',
                        sort_order='reverse')
        return items

    def get_latest_report(self, uuid):
        item = uuidToObject(uuid)
        results = item.restrictedTraverse('@@folderListing')(
            portal_type='xpose.seodash.report',
            sort_on='modified',
            sort_order='reverse')
        return results[0]

    def render_report(self, uuid):
        item = uuidToObject(uuid)
        return item.restrictedTraverse('@@content-view')()

    def can_edit(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Manager' or 'Site Administrator' in roles:
                is_adm = True
        return is_adm


class Reports(grok.View):
    grok.context(IDashboard)
    grok.require('zope2.View')
    grok.name('reports')

    def update(self):
        self.has_reports = len(self.reports()) > 0

    def reports(self):
        context = aq_inner(self.context)
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IReport.__identifier__,
                        path=dict(query='/'.join(context.getPhysicalPath()),
                                  depth=2),
                        sort_on='modified',
                        sort_order='reverse')
        return items

    def timestamp(self, uid):
        item = api.content.get(UID=uid)
        date = item.created()
        date = pydt(date)
        timestamp = {}
        timestamp['day'] = date.strftime("%d")
        timestamp['month'] = date.strftime("%m")
        timestamp['year'] = date.strftime("%Y")
        timestamp['date'] = date
        return timestamp

    def can_edit(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Manager' or 'Site Administrator' in roles:
                is_adm = True
        return is_adm


class ReportView(grok.View):
    grok.context(IDashboard)
    grok.require('cmf.ModifyPortalContent')
    grok.name('report')

    @property
    def traverse_subpath(self):
        return self.subpath

    def publishTraverse(self, request, name):
        if not hasattr(self, 'subpath'):
            self.subpath = []
        self.subpath.append(name)
        return self

    def report(self):
        uuid = self.traverse_subpath[0]
        return api.content.get(UID=uuid)

    def report_data(self):
        data = {}
        if self.report():
            item = self.report()
            data = getattr(item, 'report')
        return data


class AddReport(grok.View):
    grok.context(IDashboard)
    grok.require('cmf.ModifyPortalContent')
    grok.name('add-report')

    def render(self):
        context = aq_inner(self.context)
        uuid = self._create_report()
        next_url = '{0}/report/{1}'.format(context.absolute_url(), uuid)
        return self.request.response.redirect(next_url)

    def timestamp(self):
        date = datetime.datetime.now()
        timestamp = {}
        timestamp['month'] = date.strftime("%m")
        timestamp['year'] = date.strftime("%Y")
        return timestamp

    def _create_report(self):
        context = aq_inner(self.context)
        date = datetime.datetime.now()
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xpose.seodash.report',
            id=token,
            title='Report {0} {1}'.format(date.strftime("%B"),
                                          date.strftime("%Y")),
            container=context,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        template_file = os.path.join(os.path.dirname(__file__),
                                     'report.json')
        template = Template(open(template_file).read())
        template_vars = {
            'id': uuid_tool.uuid4(),
            'uid': uuid,
            'timestamp': int(time.time()),
            'created': datetime.datetime.now(),
            'dashboard': api.content.get_uuid(obj=context),
        }
        report = template.substitute(template_vars)
        setattr(item, 'report', report)
        modified(item)
        item.reindexObject(idxs='modified')
        return uuid
