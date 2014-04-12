from Acquisition import aq_inner
from AccessControl import Unauthorized
from five import grok
from plone import api

from zope.component import getMultiAdapter
from plone.directives import form
from plone.keyring import django_random
from plone.dexterity.content import Container
from Products.CMFPlone.utils import safe_unicode

from xpose.seodash.dashboard import IDashboard
from xpose.seotool.seotool import ISeoTool

from xpose.seodash import MessageFactory as _


class IDashboardFolder(form.Schema):
    """
    DCollection of project dashboards
    """


class DashboardFolder(Container):
    grok.implements(IDashboardFolder)


class View(grok.View):
    grok.context(IDashboardFolder)
    grok.require('zope2.View')
    grok.name('view')

    def update(self):
        self.has_dashboards = len(self.dashboards()) > 0

    def dashboards(self):
        context = aq_inner(self.context)
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        path=dict(query='/'.join(context.getPhysicalPath()),
                                  depth=1),
                        sort_on='modified',
                        sort_order='reverse')
        return items


class ManageDashboards(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('manage-dashboards')

    def update(self):
        self.has_dashboards = len(self.dashboards()) > 0

    def dashboards(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        sort_on='modified',
                        sort_order='reverse')
        return items

    def can_edit(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Manager' or 'Site Administrator' in roles:
                is_adm = True
        return is_adm


class CreateDashboard(grok.View):
    grok.context(IDashboardFolder)
    grok.require('cmf.ModifyPortalContent')
    grok.name('create-dashboard')

    def update(self):
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
                self._create_dashboard(form)

    def _create_dashboard(self, data):
        context = aq_inner(self.context)
        new_title = data['title']
        token = django_random.get_random_string(length=12)
        item = api.content.create(
            type='xpose.seodash.dashboard',
            title=new_title,
            container=context,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        #item_id = item.getId()
        #api.content.rename(obj=context[item_id],
        #                   new_id=uuid)
        url = context.absolute_url()
        base_url = url + '/@@setup-workspace?uuid=' + uuid
        next_url = base_url + '&token=' + token
        return self.request.response.redirect(next_url)
