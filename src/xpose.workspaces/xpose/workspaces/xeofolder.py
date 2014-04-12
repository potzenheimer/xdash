import contextlib
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
from urllib2 import HTTPError
from Acquisition import aq_inner
from AccessControl import Unauthorized
from five import grok
from plone import api

from zope.component import getMultiAdapter

from Products.CMFPlone.utils import safe_unicode
from plone.keyring import django_random
from plone.directives import form
from plone.dexterity.content import Container
from plone.namedfile.interfaces import IImageScaleTraversable

from xpose.workspaces import MessageFactory as _

XOVI_URI = 'https://api.xovi.net/index.php?'
BRAIN_URI = 'https://api.xovi.net/index.php?'


class IXeoFolder(form.Schema, IImageScaleTraversable):
    """
    Xeodash application folder
    """


class XeoFolder(Container):
    grok.implements(IXeoFolder)


class View(grok.View):
    grok.context(IXeoFolder)
    grok.require('cmf.ModifyPortalContent')
    grok.name('view')

    def available_services(self):
        services = {
            u'google': _(u"Google Analytics"),
            u'xovi': _(u"XOVI"),
            u'ac': _(u"activeCollab"),
        }
        data = []
        for s in services:
            item = {}
            req_key = 'xeo.cxn.{0}_api_uri'.format(s)
            api_uri = api.portal.get_registry_record(req_key)
            item['name'] = services[s]
            item['sid'] = s
            item['uri'] = api_uri
            data.append(item)
        return data

    def service_status(self, service):
        url = service['uri']
        name = service['sid']
        if name == 'ac':
            url = url + '?check_if_alive=1&format=json"'
        if name == 'xovi':
            data = {
                'key': u'myPersonalKey',
                'service': u'user',
                'method':  u'getCreditState',
                'format':  u'json',
            }
            url = url + '?' + urlencode(data)
        try:
            st = self._check_service_status(url)
        except HTTPError:
            msg = 'Not available'
        if st:
            msg = service['name'] + st
        return msg

    def _check_service_status(self, service_url):
        with contextlib.closing(urlopen(service_url)) as response:
            return response.read().decode('utf-8')


class CreateWorkspace(grok.View):
    grok.context(IXeoFolder)
    grok.require('cmf.ModifyPortalContent')
    grok.name('create-workspace')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('subject', 'email')
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
                self._create_workspace(form)

    def _create_workspace(self, data):
        context = aq_inner(self.context)
        new_title = data['title']
        token = django_random.get_random_string(length=12)
        item = api.content.create(
            type='xpose.workspaces.workspace',
            id=token,
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
