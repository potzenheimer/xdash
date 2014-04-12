from five import grok
from plone import api
from zope.component import getMultiAdapter
from zope.interface import Interface

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.interfaces import IPortalFooter

from xpose.seotool.interfaces import IXposeoTool


class NavbarViewlet(grok.Viewlet):
    grok.context(Interface)
    grok.layer(IXposeoTool)
    grok.viewletmanager(IPortalFooter)
    grok.require('zope2.View')
    grok.name('xpose.seotool.NavbarViewlet')

    def update(self):
        self.portal_url = api.portal.get().absolute_url()
        self.context_state = self.get_multi_adapter(u'plone_context_state')

    def get_multi_adapter(self, name):
        return getMultiAdapter((self.context, self.request), name=name)

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
    def user_portrait(self):
        member = api.user.get_current()
        membership = api.portal.get_tool(name="portal_membership")
        portrait = membership.getPersonalPortrait(member.getId())
        if portrait is not None:
            return portrait.absolute_url()

    @memoize
    def user_homeurl(self):
        member = api.user.get_current()
        userid = member.getId()
        return "%s/author/%s" % (api.portal.get().absolute_url(),
                                 userid)

    @memoize
    def user_actions(self):
        actions = self.context_state.actions('user')
        return [item for item in actions if item['available']]
