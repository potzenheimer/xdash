from five import grok
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFCore.utils import getToolByName


@grok.provider(IContextSourceBinder)
def possibleOrganizers(context):
    acl_users = getToolByName(context, 'acl_users')
    group = acl_users.getGroupById('organizers')
    terms = []

    if group is not None:
        for member_id in group.getMemberIds():
            user = acl_users.getUserById(member_id)
            if user is not None:
                member_name = user.getProperty('fullname') or member_id
                terms.append(SimpleVocabulary.createTerm(member_id, str(member_id), member_name))

    return SimpleVocabulary(terms)
