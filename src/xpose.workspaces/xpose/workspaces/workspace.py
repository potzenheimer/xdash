import re
import gdata
from five import grok

from z3c.form import group, field
from zope import schema
from zope.interface import invariant, Invalid
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.dexterity.content import Container
from plone.directives import dexterity, form
from plone.app.textfield import RichText
from plone.namedfile.field import NamedImage, NamedFile
from plone.namedfile.field import NamedBlobImage, NamedBlobFile
from plone.namedfile.interfaces import IImageScaleTraversable

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder

from dexterity.membrane.membrane_helpers import validate_unique_email

from xpose.workspaces import MessageFactory as _


def is_email(value):
    """ Is this an email address? """
    if not isinstance(value, basestring) or not '@' in value:
        raise Invalid(_(u"Not an email address"))
    return True


def is_url(value):
    """ Is this a URL? """
    if isinstance(value, basestring):
        pattern = re.compile(r"^https?://[^\s\r\n]+")
        if pattern.search(value.strip()):
            return True
    raise Invalid(_(u"Not a valid link"))


class IWorkspace(form.Schema, IImageScaleTraversable):
    """
    A user workspace providing protected access.
    """
    email = schema.TextLine(
        # String with validation in place looking for @, required.
        # Note that a person's email address will be their username.
        title=_(u"E-mail Address"),
        required=True,
        constraint=is_email,
    )
    first_name = schema.TextLine(
        title=_(u"First Name"),
        required=True,
    )
    last_name = schema.TextLine(
        title=_(u"Last Name"),
        required=True,
    )
    homepage = schema.TextLine(
        # url format
        title=_(u"External Homepage"),
        required=False,
        constraint=is_url,
    )
    form.widget(bio="plone.app.z3cform.wysiwyg.WysiwygFieldWidget")
    bio = schema.Text(
        title=_(u"Biography"),
        required=False,
    )

    @invariant
    def email_unique(data):
        """The email must be unique, as it is the login name (user name).

        The tricky thing is to make sure editing a user and keeping
        his email the same actually works.
        """
        user = data.__context__
        if user is not None:
            if hasattr(user, 'email') and user.email == data.email:
                # No change, fine.
                return
        error = validate_unique_email(data.email)
        if error:
            raise Invalid(error)


class Workspace(Container):
    grok.implements(IWorkspace)


class View(grok.View):
    grok.context(IWorkspace)
    grok.require('zope2.View')
    grok.name('view')

    # Add view methods here


class Analytics(grok.View):
    grok.context(IWorkspace)
    grok.require('zope2.View')
    grok.name('workspace-analytics')

    def authorized(self):
        """
        Returns True if we have an auth token, or false otherwise.
        """
        if self.context.auth_token:
            return True
        return False

    def auth_url(self):
        """
        Returns the URL used to retrieve a Google AuthSub token.
        """
        next = '%s/analytics-auth' % self.context.portal_url()
        scope = 'https://www.google.com/analytics/feeds/'
        return gdata.auth.GenerateAuthSubUrl(next,
                                             scope,
                                             secure=False,
                                             session=True)
