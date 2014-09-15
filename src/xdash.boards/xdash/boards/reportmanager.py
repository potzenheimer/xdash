import json
from Acquisition import aq_inner
from five import grok
from plone import api

from plone.keyring import django_random
from zope.lifecycleevent import modified

from xdash.boards.dashboard import IDashboard


class ReportManager(grok.View):
    grok.context(IDashboard)
    grok.require('cmf.ModifyPortalContent')
    grok.name('report-manager')

    def render(self):
        context = aq_inner(self.context)
        action = self.traverse_subpath[0]
        new_report = self.stored_report()
        if action == 'create':
            new_report = self._create_report()
        if action == 'delete':
            new_report = self._delete_report()
        if action == 'update':
            new_report = self._update_report()
        if action == 'add':
            new_report = self._add_content()
        setattr(context, 'panelPageLayout', new_report)
        modified(context)
        context.reindexObject(idxs='modified')
        row = self.traverse_subpath[1]
        base_url = context.absolute_url()
        next_url = '{0}/@@panelblock-editor/{1}'.format(base_url, row)
        return self.request.response.redirect(next_url)

    @property
    def traverse_subpath(self):
        return self.subpath

    def publishTraverse(self, request, name):
        if not hasattr(self, 'subpath'):
            self.subpath = []
        self.subpath.append(name)
        return self

    def stored_layout(self):
        context = aq_inner(self.context)
        stored = getattr(context, 'panelPageLayout')
        return stored

    def gridrow(self):
        grid = self.stored_layout()
        row = self.traverse_subpath[1]
        return grid[int(row)]

    def panels(self):
        return self.gridrow()['panels']

    def _create_report(self):
        container_uid = self.traverse_subpath[1]
        dashboard = api.content.get(UID=container_uid)
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xdash.boards.report',
            id=token,
            title=token,
            container=dashboard,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        return uuid

    def _delete_report(self):
        uuid = int(self.traverse_subpath[1])
        item = api.content.get(UID=uuid)
        api.content.delete(obj=item)
        info = {
            'status': 'success',
            'data': ''
        }
        return json.dumps(info)

    def _update_report(self):
        updated = self.stored_layout()
        row = self.gridrow()
        panels = self.panels()
        panels[0]['grid-col'] = self.traverse_subpath[2]
        panels[1]['grid-col'] = self.traverse_subpath[3]
        row['panels'] = panels
        row_idx = int(self.traverse_subpath[1])
        updated[row_idx] = row
        return updated

    def _add_content(self):
        grid = self.stored_layout()
        row_idx = self.traverse_subpath[1]
        row = grid[int(row_idx)]
        cols = self.gridrow()['panels']
        component = self.traverse_subpath[2]
        col_idx = self.traverse_subpath[3]
        col = cols[int(col_idx)]
        # Create panel content type here
        uid = self._create_panel(component)
        col['component'] = component
        col['uuid'] = uid
        col['klass'] = 'panel-column'
        row['panels'] = cols
        grid[int(row_idx)] = row
        return grid

    def _create_report_object(self):
        context = aq_inner(self.context)
        token = django_random.get_random_string(length=24)
        item = api.content.create(
            type='xdash.boards.report',
            id=token,
            title=token,
            container=context,
            safe_id=True
        )
        uuid = api.content.get_uuid(obj=item)
        return uuid
