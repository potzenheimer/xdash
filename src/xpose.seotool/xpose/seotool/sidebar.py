from Acquisition import aq_inner
from five import grok
from plone import api
from zope.interface import Interface
from plone.memoize.instance import memoize

from plone.app.uuid.utils import uuidToObject

from plone.app.layout.viewlets.interfaces import IPortalFooter

from xpose.seodash.dashboard import IDashboard
from xpose.seodash.project import IProject
from xpose.seodash.report import IReport
from xpose.seotool.seotool import ISeoTool
from xpose.seotool.interfaces import IXposeoTool


class SidebarViewlet(grok.Viewlet):
    grok.context(Interface)
    grok.layer(IXposeoTool)
    grok.viewletmanager(IPortalFooter)
    grok.require('zope2.View')
    grok.name('xpose.seotool.SidebarViewlet')

    def update(self):
        self.portal_url = api.portal.get().absolute_url()
        self.adm_url = self.portal_url + '/adm/'

    @memoize
    def user_displayname(self):
        """Get the username of the currently logged in user
        """
        if api.user.is_anonymous():
            return None
        member = api.user.get_current()
        userid = member.getId()
        fullname = userid
        fullname = member.getProperty('fullname') or fullname
        return fullname

    @memoize
    def user_homeurl(self):
        member = api.user.get_current()
        uuid = member.getProperty('dashboard')
        if uuid:
            item = uuidToObject(uuid)
            return item.absolute_url()

    def is_seotool_setup(self):
        context = aq_inner(self.context)
        return ISeoTool.providedBy(context)

    def is_dashboard(self):
        context = aq_inner(self.context)
        display = False
        ifaces = (IDashboard, IProject, IReport)
        for iface in ifaces:
            if iface.providedBy(context):
                display = True
        return display

    def is_administrator(self):
        context = aq_inner(self.context)
        is_adm = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            roles = api.user.get_roles(username=user.getId(), obj=context)
            if 'Manager' or 'Site Administrator' in roles:
                is_adm = True
        return is_adm
