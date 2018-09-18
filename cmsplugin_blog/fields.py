from django.db import models
from django.conf import settings


def _get_attached_field(self):
    from cms.models import CMSPlugin
    if not hasattr(self, '_attached_field_cache'):
        self._attached_field_cache = None

        opts = self._meta

        all_related_objects = [
            f for f in opts.get_fields()
            if (f.one_to_many or f.one_to_one)
            and f.auto_created and not f.concrete
        ]

        all_related_many_to_many_objects = [
            f for f in opts.get_fields(include_hidden=True)
            if f.many_to_many and f.auto_created
        ]

        for rel in all_related_objects + all_related_many_to_many_objects:
            if issubclass(rel.model, CMSPlugin):
                continue
            field = getattr(self, rel.get_accessor_name())
            if field.count():
                self._attached_field_cache = rel.field
    return self._attached_field_cache

def _get_attached_fields(self):
    """
    Returns an ITERATOR of all non-cmsplugin reverse foreign key related fields.
    """
    from cms.models import CMSPlugin

    opts = self._meta

    all_related_objects = [
        f for f in opts.get_fields()
        if (f.one_to_many or f.one_to_one)
        and f.auto_created and not f.concrete
    ]

    all_related_many_to_many_objects = [
        f for f in opts.get_fields(include_hidden=True)
        if f.many_to_many and f.auto_created
    ]

    for rel in all_related_objects + all_related_many_to_many_objects:
        if issubclass(rel.model, CMSPlugin):
            continue
        field = getattr(self, rel.get_accessor_name())
        if field.count():
            yield rel.field

class M2MPlaceholderField(models.ManyToManyField):

    def __init__(self, **kwargs):

        if 'actions' in kwargs:
            self.actions = kwargs.pop('actions')

        if 'placeholders' in kwargs:
            self.placeholders = kwargs.pop('placeholders')

        kwargs['editable'] = False

        if 'to' in kwargs:
            del kwargs['to']

        super(M2MPlaceholderField, self).__init__('cms.Placeholder', **kwargs)

    def contribute_to_related_class(self, cls, related):
        setattr(cls, '_get_attached_field', _get_attached_field)
        setattr(cls, '_get_attached_fields', _get_attached_fields)
        super(M2MPlaceholderField, self).contribute_to_related_class(cls, related)

if "south" in settings.INSTALLED_APPS:

    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["^cmsplugin_blog\.fields",])
