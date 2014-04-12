from plone import api


def setupGroups(portal):
    if not api.group.get(groupname='staff'):
        api.group.create(
            groupname='staff',
            title='Xpose414 Staff',
            roles=['Readers', ],
            groups=['Site Administrators', ],
        )
        api.group.create(
            groupname='customers',
            title='Customers',
            roles=['Readers', ],
        )


def importVarious(context):
    """Miscellanous steps import handle
    """
    if context.readDataFile('xpose.seotool-various.txt') is None:
        return
    portal = api.portal.get()
    setupGroups(portal)
