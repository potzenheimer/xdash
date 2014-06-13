import json
from Acquisition import aq_inner
from AccessControl import Unauthorized
from five import grok
from plone import api

from plone.keyring import django_random
from zope.component import getMultiAdapter
from zope.lifecycleevent import modified

from Products.CMFPlone.utils import safe_unicode

from Products.statusmessages.interfaces import IStatusMessage
from xpose.seodash.dashboard import IDashboard
from xpose.seotool.seotool import ISeoTool

from xpose.seotool import MessageFactory as _


class ManageDashboards(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('manage-dashboards')

    def update(self):
        self.has_dashboards = len(self.dashboards()) > 0
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('ga.profile')
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
                    if not form[value] and value in required:
                        error = {}
                        error['active'] = True
                        error['msg'] = _(u"This field is required")
                        form_errors[value] = error
                        errorIdx += 1
                    else:
                        error = {}
                        error['active'] = False
                        error['msg'] = form[value]
                        form_errors[value] = error
            if errorIdx > 0:
                self.errors = form_errors
            else:
                self._update_dashboard(form)

    def has_token(self):
        token = False
        if self.request.get('uuid'):
            token = True
        return token

    def dashboard(self):
        uuid = self.request.get('uuid')
        return api.content.get(UID=uuid)

    def dashboard_name(self):
        if self.has_token():
            item = self.dashboard()
            return item.Title()
        return _(u"Untitled dashboard")

    def dashboard_settings(self):
        if self.has_token():
            item = self.dashboard()
            data = getattr(item, 'projects')
            return data

    def dashboards(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        sort_on='modified',
                        sort_order='reverse')
        return items

    def ga_profiles(self):
        portal = api.portal.get()
        item = portal['adm']
        stored = getattr(item, 'projects_ga')
        return json.loads(stored)

    def _update_dashboard(self, data):
        uuid = data['uuid']
        context = api.content.get(UID=uuid)
        setattr(context, 'ga_id', data['ga-profile'])
        modified(context)
        context.reindexObject(idxs='modified')
        IStatusMessage(self.request).addStatusMessage(
            _(u"GA configuration has sucessfully been refreshed"),
            type='info')
        portal_url = api.portal.get().absolute_url()
        url = '{0}/adm/@@manage-dashboards'.format(portal_url)
        return self.request.response.redirect(url)

    def can_edit(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Manager' or 'Site Administrator' in roles:
                is_adm = True
        return is_adm


class EditDashboard(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('edit-dashboard')

    def render(self):
        context = aq_inner(self.context)
        uuid = self.traverse_subpath[0]
        action = self.traverse_subpath[1]
        next_url = context.absolute_url()
        if action == 'create':
            next_url = self._create_project(uuid)
        if action == 'delete':
            next_url = self._delete_project(uuid)
        return self.request.response.redirect(next_url)

    @property
    def traverse_subpath(self):
        return self.subpath

    def publishTraverse(self, request, name):
        if not hasattr(self, 'subpath'):
            self.subpath = []
        self.subpath.append(name)
        return self

    def _delete_project(self, uuid):
        context = aq_inner(self.context)
        item = api.content.get(UID=uuid)
        data = getattr(item, 'projects')
        idx = self.traverse_subpath[2]
        data.pop(int(idx))
        setattr(item, 'projects', data)
        url = '{0}/@@manage-dashboards?uuid={1}'.format(
            context.absolute_url(), uuid)
        return url


class AddProjects(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('add-project')

    def update(self):
        self.has_dashboard = len(self.dashboard()) > 0
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('title')
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
                    if not form[value] and value in required:
                        error = {}
                        error['active'] = True
                        error['msg'] = _(u"This field is required")
                        form_errors[value] = error
                        errorIdx += 1
                    else:
                        error = {}
                        error['active'] = False
                        error['msg'] = form[value]
                        form_errors[value] = error
            if errorIdx > 0:
                self.errors = form_errors
            else:
                self._update_dashboard(form)

    @property
    def traverse_subpath(self):
        return self.subpath

    def publishTraverse(self, request, name):
        if not hasattr(self, 'subpath'):
            self.subpath = []
        self.subpath.append(name)
        return self

    def dashboard(self):
        uuid = self.traverse_subpath[0]
        return api.content.get(UID=uuid)

    def dashboard_name(self):
        if self.dashboard():
            item = self.dashboard()
            return item.Title()
        return _(u"Untitled dashboard")

    def project_infos(self):
        item = self.dashboard()
        return getattr(item, 'projects')

    def _update_dashboard(self, data):
        context = aq_inner(self.context)
        item_uid = self.traverse_subpath[0]
        item = api.content.get(UID=item_uid)
        token = django_random.get_random_string(length=24)
        project = {
            'id': token,
            'title': data['title'],
            'ga': '',
            'xo': data['title'],
            'ac': data['title']
        }
        items = getattr(item, 'projects', None)
        if items is None:
            items = list()
        items.append(project)
        setattr(item, 'projects', items)
        modified(item)
        item.reindexObject(idxs='modified')
        base_url = context.absolute_url()
        url = '{0}/@@manage-dashboards?uuid={1}'.format(base_url, item_uid)
        return self.request.response.redirect(url)
