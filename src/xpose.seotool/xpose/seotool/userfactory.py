from Acquisition import aq_inner
from five import grok
from plone import api
from zope import schema
from zope.component import getUtility


from plone.directives import form
from plone.keyring import django_random
from z3c.form import button

from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from Products.statusmessages.interfaces import IStatusMessage

from xpose.seotool.seotool import ISeoTool

from xpose.seotool import MessageFactory as _

usergroups = SimpleVocabulary([
    SimpleTerm(value=u'staff', title=_(u'Xpose414 Staff')),
    SimpleTerm(value=u'customers', title=_(u'Customers'))
])


class IUserCreation(form.Schema):

    fullname = schema.TextLine(
        title=_(u"Fullname"),
        required=False,
    )
    email = schema.TextLine(
        title=_(u"E-Mail"),
        description=_(u"Enter a valid E-Mail address. Note: this address will "
                      u"act as the login name"),
        required=True,
    )
    usergroup = schema.Choice(
        title=_(u"User Group"),
        description=_(u"Please select the user group this user should be "
                      u"added to as a member"),
        source=usergroups,
        required=True,
        default=u'customers',
    )


class UserCreationForm(form.SchemaEditForm):
    grok.context(ISeoTool)
    grok.require('cmf.AddPortalContent')
    grok.name('create-user')

    schema = IUserCreation
    ignoreContext = True
    css_class = 'app-form app-form-create'

    label = _(u"Add new user account")

    def updateActions(self):
        super(UserCreationForm, self).updateActions()
        self.actions['save'].addClass("btn btn-primary btn-editpanel")
        self.actions['cancel'].addClass("btn btn-link")

    @button.buttonAndHandler(_(u"Save"), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)

    @button.buttonAndHandler(_(u"cancel"))
    def handleCancel(self, action):
        context = aq_inner(self.context)
        IStatusMessage(self.request).addStatusMessage(
            _(u"User creation has been cancelled."),
            type='info')
        return self.request.response.redirect(context.absolute_url())

    def applyChanges(self, data):
        context = aq_inner(self.context)
        user_id = django_random.get_random_string(length=12)
        properties = dict(
            fullname=data['fullname'],
        )
        user = api.user.create(
            username=data['email'],
            email=data['email'],
            properties=properties,
        )
        api.group.add_user(
            groupname=data['usergroup'],
            username=user.getId()
        )
        IStatusMessage(self.request).addStatusMessage(
            _(u"New user account has been created succesfully"),
            type='info')
        next_url = context.absolute_url() + '/@@manage-users'
        return self.request.response.redirect(next_url)
