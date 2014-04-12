from five import grok
from plone import api

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


from xpose.seodash import MessageFactory as _


# Interface class; used to define content-type schema.

class IProject(form.Schema, IImageScaleTraversable):
    """
    A single project usually a single site
    """


class Project(Container):
    grok.implements(IProject)


class View(grok.View):
    grok.context(IProject)
    grok.require('zope2.View')
    grok.name('view')

    def user_details(self):
        user = api.user.get_current()
        import pdb; pdb.set_trace( )
        return user
