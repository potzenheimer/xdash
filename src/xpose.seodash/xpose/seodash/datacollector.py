from Acquisition import aq_inner
from five import grok
from plone import api

from plone.keyring import django_random

from plone.app.contentlisting.interfaces import IContentListing

from xpose.seodash.dashboardfolder import IDashboardFolder
from xpose.seodash.dashboard import IDashboard


class DataCollector(grok.View):
    grok.context(IDashboardFolder)
    grok.require('zope2.View')
    grok.name('data-collector')

    def render(self):
        context = aq_inner(self.context)
        if len(self.dashboards()) > 0:
            reports = self._collect()
        next_url = context.absolute_url()
        return self.request.response.redirect(next_url + '?created=' + reports)

    def dashboards(self):
        context = aq_inner(self.context)
        catalog = api.portal.get_tool(name='portal_catalog')
        items = catalog(object_provides=IDashboard.__identifier__,
                        path=dict(query='/'.join(context.getPhysicalPath()),
                                  depth=1))
        return IContentListing(items)

    def _collect(self):
        idx = 0
        dashboards = self.dashboards()
        for board in dashboards:
            projects = getattr(board, 'projects')
            if len(projects):
                for p in projects:
                    import pdb; pdb.set_trace()
                    report_obj = self._create_report()
        return idx

    def _create_report(self):
        context = aq_inner(self.context)
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xpose.seodash.report',
            id=token,
            title='report-{0}'.format(token),
            container=context,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        return uuid
