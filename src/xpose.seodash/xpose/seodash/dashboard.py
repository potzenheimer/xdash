from Acquisition import aq_inner
from AccessControl import Unauthorized
from five import grok
from plone import api

from zope import schema
from zope.component import getMultiAdapter

from plone.dexterity.content import Container
from plone.directives import form
from plone.namedfile.field import NamedBlobImage
from plone.namedfile.interfaces import IImageScaleTraversable

from plone.keyring import django_random
from Products.CMFPlone.utils import safe_unicode
from plone.app.uuid.utils import uuidToObject

from xpose.seodash.project import IProject
from xpose.seodash.report import IReport

from xpose.seodash import MessageFactory as _


class IDashboard(form.Schema, IImageScaleTraversable):
    """
    A project dashboard
    """
    ga_id = schema.TextLine(
        title=_(u"GA Site ID"),
        required=False,
    )
    projects = schema.TextLine(
        title=_(u"Dashboard settings"),
        description=_(u"Settings containing a project list"),
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
        self.has_projects = len(self.projects()) > 0
        self.show_projectlist = len(self.projects()) > 1

    def has_reports(self, uuid):
        container = api.content.get(UID=uuid)
        return len(container.items()) > 0

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

    def active_project(self):
        return self.projects()[0]

    def projects(self):
        context = aq_inner(self.context)
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IProject.__identifier__,
                        path=dict(query='/'.join(context.getPhysicalPath()),
                                  depth=1),
                        sort_on='getObjPositionInParent')
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

    def can_edit(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Manager' or 'Site Administrator' in roles:
                is_adm = True
        return is_adm


class CreateProject(grok.View):
    grok.context(IDashboard)
    grok.require('cmf.ModifyPortalContent')
    grok.name('create-project')

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
                self._create_project(form)

    def _create_project(self, data):
        context = aq_inner(self.context)
        new_title = data['title']
        token = django_random.get_random_string(length=12)
        api.content.create(
            type='xpose.seodash.project',
            id=token,
            title=new_title,
            container=context,
            safe_id=True
        )
        url = context.absolute_url()
        return self.request.response.redirect(url)
