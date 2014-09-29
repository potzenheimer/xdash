# -*- coding: utf-8 -*-
"""Module for report management"""

import json

from AccessControl import Unauthorized
from Acquisition import aq_inner
from Products.CMFPlone.utils import safe_unicode
from five import grok
from plone import api
from plone.keyring import django_random
from plone.event.utils import pydt
from zope.component import getMultiAdapter
from zope.lifecycleevent import modified

from Products.CMFCore.interfaces import IContentish

from xpose.seodash.dashboard import IDashboard
from xpose.seodash.report import IReport

from xpose.seotool import MessageFactory as _


class ReportManager(grok.View):
    grok.context(IDashboard)
    grok.require('cmf.ModifyPortalContent')
    grok.name('report-manager')

    def render(self):
        context = aq_inner(self.context)
        action = self.traverse_subpath[0]
        new_report = self.stored_report()
        if action == 'create':
            new_report = self._create_report()
        if action == 'delete':
            new_report = self._delete_report()
        if action == 'update':
            new_report = self._update_report()
        if action == 'add':
            new_report = self._add_content()
        setattr(context, 'panelPageLayout', new_report)
        modified(context)
        context.reindexObject(idxs='modified')
        row = self.traverse_subpath[1]
        base_url = context.absolute_url()
        next_url = '{0}/@@panelblock-editor/{1}'.format(base_url, row)
        return self.request.response.redirect(next_url)

    @property
    def traverse_subpath(self):
        return self.subpath

    def publishTraverse(self, request, name):
        if not hasattr(self, 'subpath'):
            self.subpath = []
        self.subpath.append(name)
        return self

    def stored_layout(self):
        context = aq_inner(self.context)
        stored = getattr(context, 'panelPageLayout')
        return stored

    def gridrow(self):
        grid = self.stored_layout()
        row = self.traverse_subpath[1]
        return grid[int(row)]

    def panels(self):
        return self.gridrow()['panels']

    def _create_report(self):
        container_uid = self.traverse_subpath[1]
        dashboard = api.content.get(UID=container_uid)
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xpose.seodash.report',
            id=token,
            title=token,
            container=dashboard,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        return uuid

    def _delete_report(self):
        uuid = int(self.traverse_subpath[1])
        item = api.content.get(UID=uuid)
        api.content.delete(obj=item)
        info = {
            'status': 'success',
            'data': ''
        }
        return json.dumps(info)

    def _update_report(self):
        updated = self.stored_layout()
        row = self.gridrow()
        panels = self.panels()
        panels[0]['grid-col'] = self.traverse_subpath[2]
        panels[1]['grid-col'] = self.traverse_subpath[3]
        row['panels'] = panels
        row_idx = int(self.traverse_subpath[1])
        updated[row_idx] = row
        return updated

    def _add_content(self):
        grid = self.stored_layout()
        row_idx = self.traverse_subpath[1]
        row = grid[int(row_idx)]
        cols = self.gridrow()['panels']
        component = self.traverse_subpath[2]
        col_idx = self.traverse_subpath[3]
        col = cols[int(col_idx)]
        # Create panel content type here
        uid = self._create_panel(component)
        col['component'] = component
        col['uuid'] = uid
        col['klass'] = 'panel-column'
        row['panels'] = cols
        grid[int(row_idx)] = row
        return grid

    def _create_report_object(self):
        context = aq_inner(self.context)
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xpose.seodash.report',
            id=token,
            title=token,
            container=context,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        return uuid


class LinkBuilding(grok.View):
    grok.context(IReport)
    grok.require('zope2.View')
    grok.name('report-editor-links')

    def update(self):
        self.has_report = len(self.report()) > 0
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        if 'form.button.Submit' in self.request:
            authenticator = getMultiAdapter((context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized
            form = self.request.form
            form_data = {}
            form_errors = {}
            errorIdx = 0
            for value in form:
                if value not in unwanted:
                    form_data[value] = safe_unicode(form[value])
            if errorIdx > 0:
                self.errors = form_errors
            else:
                self._update_report_data(form_data)

    def report(self):
        context = aq_inner(self.context)
        data = []
        stored_report = getattr(context, 'report', None)
        if stored_report is not None:
            report = json.loads(stored_report)
            metrics = report['items']
            data = metrics[0]
        return data

    def _update_report_data(self, data):
        context = aq_inner(self.context)
        metric = self.report()
        new_row = {
            'xd:linkDate': data['lb-date'],
            'xd:linkSourceURI': data['lb-source'],
            'xd:linkTargetURI': data['lb-target'],
            'xd:linkText': data['lb-text']
        }
        table = metric['dataTable']
        rows = table['rows']
        rows.append(new_row)
        table['rows'] = rows
        metric['dataTable'] = table
        stored = getattr(context, 'report')
        data = json.loads(stored)
        items = data['items']
        items[0] = metric
        setattr(context, 'report', json.dumps(data))
        modified(context)
        context.reindexObject(idxs='modified')
        msg = _(u"Built links data table was successfully updated")
        api.portal.show_message(msg, self.request)
        portal_url = api.portal.get().absolute_url()
        url = '{0}/adm/'.format(portal_url)
        return self.request.response.redirect(url)


class ReviewQueue(grok.View):
    grok.context(IContentish)
    grok.require('cmf.ModifyPortalContent')
    grok.name('review-queue')

    def update(self):
        self.has_reports = self.unapproved_reports_index() > 0

    def unapproved_reports(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IReport.__identifier__,
                        approved=False,
                        sort_on='modified',
                        sort_order='reverse')
        return items

    def unapproved_reports_index(self):
        return len(self.unapproved_reports())

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

    def breadcrumbs(self, item):
        obj = item.getObject()
        view = getMultiAdapter((obj, self.request), name='breadcrumbs_view')
        # cut off the item itself
        breadcrumbs = list(view.breadcrumbs())[:-1]
        if len(breadcrumbs) == 0:
            # don't show breadcrumbs if we only have a single element
            return None
        if len(breadcrumbs) > 3:
            # if we have too long breadcrumbs, emit the middle elements
            empty = {'absolute_url': '', 'Title': unicode('…', 'utf-8')}
            breadcrumbs = [breadcrumbs[0], empty] + breadcrumbs[-2:]
        return breadcrumbs


class ReportReview(grok.View):
    grok.context(IDashboard)
    grok.require('cmf.ModifyPortalContent')
    grok.name('report-review')

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

    def project_id(self):
        report = self.report()
        return getattr(report, 'projectId', 'undefined')

    def report_data(self):
        data = {}
        if self.report():
            item = self.report()
            data = getattr(item, 'report')
        return data
