from Acquisition import aq_inner
from AccessControl import Unauthorized
from five import grok
from plone import api

from zope.component import getMultiAdapter
from zope.schema.vocabulary import SimpleVocabulary

from Products.CMFPlone.utils import safe_unicode
from plone.app.uuid.utils import uuidToObject

from zope.schema.interfaces import IContextSourceBinder
from Products.statusmessages.interfaces import IStatusMessage

from xpose.seodash.dashboard import IDashboard
from xpose.seotool.seotool import ISeoTool

from xpose.seodash import MessageFactory as _


class UserManager(grok.View):
    grok.context(ISeoTool)
    grok.require('cmf.ManagePortal')
    grok.name('manage-users')

    def update(self):
        self.has_users = len(self.customers()) > 0

    def customers(self):
        return api.user.get_users(groupname='customers')

    def get_userdetails(self, user):
        user_id = user.getId()
        user = api.user.get(username=user_id)
        info = {}
        info['user_id'] = user_id
        info['dashboard'] = user.getProperty('dashboard')
        info['email'] = user.getProperty('email')
        info['name'] = user.getProperty('fullname')
        return info

    def compute_dashboard(self, uuid):
        dashboard = uuidToObject(uuid)
        return dashboard


class UserPermissionManager(grok.View):
    grok.context(ISeoTool)
    grok.require('cmf.ManagePortal')
    grok.name('manage-user-permissions')

    def update(self):
        self.user_id = self.request.get('user', None)
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit', 'form.button.Clear')
        required = ('panel')
        if 'form.button.Clear' in self.request:
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
            self._clear_dashboard_asignment(form_data)
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
                self._update_dashboard_asignment(form)

    def default_value(self, error):
        value = self.uuid
        if error['active'] is False:
            value = error['msg']
        return value

    def has_asignment(self):
        value = False
        info = self.get_userdetails()
        if info['dashboard']:
            value = True
        return value

    def is_selected(self, value):
        selected = False
        return selected

    def _update_dashboard_asignment(self, data):
        context = aq_inner(self.context)
        user = api.user.get(username=self.user_id)
        properties = {'dashboard': data['dashboard']}
        user.setMemberProperties(mapping=properties)
        dashboard = uuidToObject(data['dashboard'])
        api.user.grant_roles(
            username=self.user_id,
            roles=['Reader'],
            obj=dashboard
        )
        IStatusMessage(self.request).addStatusMessage(
            _(u"User has been granted dashboard access"),
            type='info')
        base_url = context.absolute_url()
        params = '/@@manage-users?user={0}'.format(self.user_id)
        next_url = base_url + params
        return self.request.response.redirect(next_url)

    def _clear_dashboard_asignment(self, data):
        context = aq_inner(self.context)
        user = api.user.get(username=self.user_id)
        properties = dict(
            dashboard='',
        )
        user.setMemberProperties(properties)
        IStatusMessage(self.request).addStatusMessage(
            _(u"Dashboard acces has been revoked"),
            type='info')
        base_url = context.absolute_url()
        params = '/@@manage-users?user={0}'.format(self.user_id)
        next_url = base_url + params
        return self.request.response.redirect(next_url)

    def get_userdetails(self):
        user = api.user.get(username=self.user_id)
        info = {}
        info['user_id'] = self.user_id
        info['dashboard'] = user.getProperty('dashboard')
        info['email'] = user.getProperty('email')
        info['name'] = user.getProperty('fullname')
        return info

    def dashboards(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        sort_on='modified',
                        sort_order='reverse')
        return items


class GroupMembers(object):
    """ Context source binder to provide a vocabulary of users in a given
        group.
    """
    grok.implements(IContextSourceBinder)

    def __init__(self, group_name):
        self.group_name = group_name

    def __call__(self, context):
        group = api.group.get(groupname=self.group_name)
        terms = []
        if group is not None:
            for member_id in api.user.get_users(groupname=group):
                user = api.user.get(username=member_id)
                if user is not None:
                    member_name = user.getProperty('fullname') or member_id
                    terms.append(SimpleVocabulary.createTerm(
                        member_id, str(member_id), member_name)
                    )

        return SimpleVocabulary(terms)
