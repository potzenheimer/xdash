from Acquisition import aq_inner
from five import grok
from plone import api

from plone.app.uuid.utils import uuidToObject
from plone.memoize.instance import memoize
from plone.app.layout.navigation.interfaces import INavigationRoot


class FrontPageView(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('frontpage-router')

    def update(self):
        self.next_url = self.redirection_target()

    def render(self):
        return self.request.response.redirect(self.next_url)

    def redirection_target(self):
        portal_url = api.portal.get().absolute_url()
        if api.user.is_anonymous():
            url = portal_url + '/login'
        else:
            if self.is_administrator() is True:
                if not self.first_visit():
                    url = portal_url + '/@@setup-seotool'
                else:
                    url = portal_url + '/adm'
            else:
                url = self.user_homeurl()
        return url

    @memoize
    def user_homeurl(self):
        member = api.user.get_current()
        uuid = member.getProperty('dashboard')
        if uuid:
            item = uuidToObject(uuid)
            return item.absolute_url()

    def is_administrator(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Site Administrator' in roles:
                is_adm = True
            if 'Manager' in roles:
                is_adm = True
        return is_adm

    def first_visit(self):
        portal = api.portal.get()
        return portal.hasObject('adm')


class SetupSeoTool(grok.View):
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')
    grok.name('setup-seotool')


class SetupTool(grok.View):
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')
    grok.name('setup-tool')

    def render(self):
        portal = api.portal.get()
        success_url = portal.absolute_url() + '/adm'
        api.content.create(
            type='xpose.seotool.seotool',
            id='adm',
            title=u'Settings',
            container=portal,
            safe_id=True
        )
        api.content.create(
            type='xpose.seodash.dashboardfolder',
            id='xd',
            title=u'Dashboards',
            container=portal,
            safe_id=True
        )
        return self.request.response.redirect(success_url)
