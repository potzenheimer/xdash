import json
import contextlib

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from Acquisition import aq_inner
from AccessControl import Unauthorized
from five import grok
from plone import api
from zope import schema
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.lifecycleevent import modified
from plone.directives import form
from plone.dexterity.content import Container
from Products.CMFPlone.utils import safe_unicode

from plone.namedfile.interfaces import IImageScaleTraversable
from Products.statusmessages.interfaces import IStatusMessage

from xpose.seodash.dashboard import IDashboard
from xpose.seodash.report import IReport

from xpose.seotool.ac import IACTool
from xpose.seotool.ga import IGATool
from xpose.seotool.xovi import IXoviTool

from xpose.seotool import MessageFactory as _


class ISeoTool(form.Schema, IImageScaleTraversable):
    """
    Seo Application utility tool
    """
    projects_ac = schema.TextLine(
        title=_(u"activeCollab Projects"),
        description=_(u"A list of available projects from the configured "
                      u"activeCollab account. Do not change this manually"),
        required=False,
    )
    projects_ga = schema.TextLine(
        title=_(u"GA profiles"),
        description=_(u"List of available Google Analytics profiles."),
        required=False,
    )
    projects_xovi = schema.TextLine(
        title=_(u"Xovi Projects"),
        description=_(u"A list of available projects from the configured xovi "
                      u"account in json format. Do not change this manually"),
        required=False,
    )
    domains_xovi = schema.TextLine(
        title=_(u"Xovi Domains"),
        required=False,
    )


class SeoTool(Container):
    grok.implements(ISeoTool)


class View(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('view')

    def update(self):
        self.has_reports = self.unapproved_reports_index() > 0
        self.has_dashboards = len(self.dashboards()) > 0

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
        sid = service['sid']
        services = self.service_details()
        api = services[sid]
        tool = getUtility(api['iface'])
        return tool.status()

    def get_state_klass(self, statuscode):
        state = {'statuscode': 'available',
                 'klass': 'text-success'}
        if statuscode == 'Not available':
            state = {'statuscode': 'not available',
                     'klass': 'text-danger'}
        return state

    def _check_service_status(self, service_url):
        with contextlib.closing(urlopen(service_url)) as response:
            return response.read().decode('utf-8')

    def service_details(self):
        data = {
            'ac': {
                u'id': u"ac",
                u'name': _(u"activeCollab"),
                u'iface': IACTool,
            },
            'google': {
                u'id': u"ga",
                u'name': _(u"Google Analytics"),
                u'iface': IGATool,
            },
            'xovi': {
                u'id': u"xovi",
                u'name': _(u"XOVI"),
                u'iface': IXoviTool,
            },
        }
        return data

    def unapproved_reports(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IReport.__identifier__,
                        approved=False,
                        sort_on='modified',
                        sort_order='reverse')
        return items

    def unapproved_reports_index(self):
        return len(self.unapproved_reports())

    def dashboards(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        sort_on='modified',
                        sort_order='reverse')
        return items


class SetupServices(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('setup-services')

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
        name = service['sid']
        status = 'OK'
        info = {}
        if name == 'xovi':
            xovi_tool = getUtility(IXoviTool)
            info = xovi_tool.status()
        if name == 'ac':
            ac_tool = getUtility(IACTool)
            info = ac_tool.status()
        status = info
        return status

    def get_state_klass(self, statuscode):
        state = {'statuscode': 'active',
                 'klass': 'text-success'}
        if statuscode == 'Not available':
            state = {'statuscode': 'not available',
                     'klass': 'text-danger'}
        return state


class AddAuthToken(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('add-auth-token')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('service')
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
                self._set_auth_token(form)

    def _set_auth_token(self, data):
        service = data['service']
        if service == 'google':
            client_id = data['client_id']
            client_secret = data['client_secret']
            record_id = 'xeo.cxn.{0}_client_id'.format(service)
            record_secret = 'xeo.cxn.{0}_client_secret'.format(service)
            api.portal.set_registry_record(record_id, client_id)
            api.portal.set_registry_record(record_secret, client_secret)
        else:
            token = data['token']
            record = 'xeo.cxn.{0}_client_key'.format(service)
            api.portal.set_registry_record(record, token)
        portal_url = api.portal.get().absolute_url()
        param = '/adm/@@setup-{0}'.format(service)
        url = portal_url + param
        return self.request.response.redirect(url)


class SetupAnalytics(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('setup-google')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('service')
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
                self._refresh_configuration(form)

    def available_profiles(self):
        context = aq_inner(self.context)
        stored = getattr(context, 'projects_ga')
        data = json.loads(stored)
        return data

    def webproperties(self, acc_id):
        tool = getUtility(IGATool)
        data = tool.get(account_id=acc_id)
        return data

    def profiles(self, acc_id, property_id):
        tool = getUtility(IGATool)
        data = tool.get(
            account_id=acc_id,
            property_id=property_id
        )
        return data

    def get_profiles(self):
        tool = getUtility(IGATool)
        accounts = tool.get(qt='accounts')
        data = []
        idx = 0
        if accounts.get('items'):
            for item in accounts.get('items'):
                item_id = item.get('id')
                props = tool.get(
                    qt='properties',
                    account_id=item_id)
                if props.get('items'):
                    for x in props.get('items'):
                        profiles = tool.get(
                            qt='profiles',
                            account_id=item_id,
                            property_id=x.get('id'))
                        if profiles.get('items'):
                            for x in profiles.get('items'):
                                idx += 1
                                info = {}
                                info['idx'] = idx
                                info['id'] = x['id']
                                info['name'] = x['name']
                                data.append(info)
        return data

    def get_metrics(self):
        base_uri = 'https://www.googleapis.com/analytics/v3/'
        url = '{0}metadata/ga/columns?pp=1'.format(base_uri)
        with contextlib.closing(urlopen(url)) as response:
            resp = response.read().decode('utf-8')
            data = json.loads(resp)
            return data

    def get_stateklass(self, code):
        klass = 'text-success'
        if code == 'DEPRECATED':
            klass = 'text-danger'
        return klass

    def _refresh_configuration(self, data):
        context = aq_inner(self.context)
        project_list = self.get_profiles()
        projects = json.dumps(project_list)
        setattr(context, 'projects_ga', projects)
        modified(context)
        context.reindexObject(idxs='modified')
        IStatusMessage(self.request).addStatusMessage(
            _(u"GA configuration has sucessfully been refreshed"),
            type='info')
        portal_url = api.portal.get().absolute_url()
        url = '{0}/adm/@@setup-google'.format(portal_url)
        return self.request.response.redirect(url)


class SetupXovi(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('setup-xovi')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('service')
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
                self._refresh_configuration(form)

    def service_status(self):
        xovi_tool = getUtility(IXoviTool)
        info = xovi_tool.status()
        return info

    def _refresh_configuration(self, data):
        context = aq_inner(self.context)
        xovi_tool = getUtility(IXoviTool)
        project_list = xovi_tool.get(
            service=u'project',
            method=u'getProjects',
            limit=50
        )
        projects = json.dumps(project_list)
        setattr(context, 'projects_xovi', projects)
        daily_domains = xovi_tool.get(
            service=u'seo',
            method=u'getDailyDomains',
            limit=50
        )
        domains = json.dumps(daily_domains)
        setattr(context, 'domains_xovi', domains)
        modified(context)
        context.reindexObject(idxs='modified')
        IStatusMessage(self.request).addStatusMessage(
            _(u"The Xovi configuration has sucessfully been refreshed"),
            type='info')
        portal_url = api.portal.get().absolute_url()
        param = '/adm/@@setup-xovi'
        url = portal_url + param
        return self.request.response.redirect(url)

    def available_projects(self):
        context = aq_inner(self.context)
        project_info = getattr(context, 'projects_xovi', '')
        data = json.loads(project_info)
        items = []
        for x in data['apiResult']:
            info = {}
            info['id'] = x['id']
            info['project'] = x['name']
            items.append(info)
        return items

    def available_domains(self):
        context = aq_inner(self.context)
        project_info = getattr(context, 'domains_xovi', '')
        data = json.loads(project_info)
        items = []
        for x in data['apiResult']:
            info = {}
            info['domain'] = x['domain']
            items.append(info)
        return items


class SetupAC(grok.View):
    grok.context(ISeoTool)
    grok.require('zope2.View')
    grok.name('setup-ac')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = ('service')
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
                self._refresh_configuration(form)

    def service_status(self):
        xovi_tool = getUtility(IACTool)
        info = xovi_tool.status()
        return info

    def _refresh_configuration(self, data):
        context = aq_inner(self.context)
        xovi_tool = getUtility(IACTool)
        project_list = xovi_tool.make_request(path_info=u'projects')
        projects = json.dumps(project_list)
        setattr(context, 'projects_ac', projects)
        modified(context)
        context.reindexObject(idxs='modified')
        IStatusMessage(self.request).addStatusMessage(
            _(u"The activeCollab configuration was sucessfully refreshed"),
            type='info')
        portal_url = api.portal.get().absolute_url()
        param = '/adm/@@setup-ac'
        url = portal_url + param
        return self.request.response.redirect(url)

    def available_projects(self):
        context = aq_inner(self.context)
        project_info = getattr(context, 'projects_ac', '')
        data = json.loads(project_info)
        items = data
        return items

    def recent_activity(self, project_id):
        pinfo = u'projects/{0}/tracking'.format(project_id)
        xovi_tool = getUtility(IACTool)
        data = xovi_tool.make_request(path_info=pinfo)
        info = []
        if data:
            for entry in data[:10]:
                info.append(entry)
        return info
