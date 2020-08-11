from django.db.models import Model, Manager, ForeignKey, CharField, DateTimeField, CASCADE, DO_NOTHING
from django.conf import settings

class DataConsistencyError(RuntimeError): pass

class GetOrCreateWChecksManager(Manager):
    "Manager class that provides `get_or_create_with_checks()`"
        
    def get_or_create_with_checks(self, non_key_values = {}, **key):
        """Same as `Model.objects.get_or_create()`, but also checks if `non_key_values` match those in the database if the object already exists."""
        existing, created = self.get_or_create(**key, defaults = non_key_values)
        if not created:
            different_fields = {}
            for k, v in non_key_values.items():
                existing_v = getattr(existing, k)
                if v != existing_v:
                    different_fields[k] = (v, existing_v)

            if different_fields:
                raise DataConsistencyError('New row for {:} with key {:} differs from data in database on fields:\n{:}'
                                           .format(self.model.__name__, str(key), str(different_fields)))

        return existing, created

class ModelWChecksManager(Model):
    "Abstract Manager class that uses GetOrCreateWChecksManager Manager so that `get_or_create_with_checks()` is available by default"
    objects = GetOrCreateWChecksManager()
    
    class Meta:
        abstract = True

def ForeignKey_CD(*args, **kwargs):
    "A shortcut for on_delete=CASCADE"
    return ForeignKey(*args, on_delete = CASCADE, **kwargs)
    
class AtLeastOneNotNullMixin(object):
    """Model Mixin class that overrides default django form "clean" method to ensure that at least one of several fields is not NULL (or False)
    
    Fields that are checked should be set in a class attribute "joint_not_nulls" on the model as a list of lists containing fields to check
    
    e.g. the following would make sure that at least one of field 1&2 is not null, and at least one of field 3,4&5 is not null
    
    joint_not_nulls = [("field1", "field2",),
                       ("field3", "field4", "field5")]"""
    def clean(self):
        super().clean()

        for fields in self.joint_not_nulls:
            all_null = True
            for f in fields:
                if getattr(self, f) not in [None, False]:
                    all_null = False
                    break
            
            if all_null:
                raise ValidationError('At least one of the following must be provided: %s' % ', '.join(fields))
                
class AddedByMixin(Model):
    "Abstract Model base class that provides added_by/date_added fields"
    added_by = ForeignKey(settings.AUTH_USER_MODEL, blank=True, on_delete=DO_NOTHING)
    date_added = DateTimeField(auto_now_add=True)

    class AdminMixin(object):
        def save_model(self, request, obj, form, change):
            if not obj.pk:
                # Only set added_by during the first save.
                obj.added_by = request.user
            super().save_model(request, obj, form, change)
            
        readonly_fields = ["added_by", "date_added"]
        
        list_filter = ["added_by"]
        
    class Meta:
        abstract = True
        
#a custom model base list, can be used like this: `class MyModel(*DefaultModelBases): pass`
DefaultModelBases = (ModelWChecksManager, )

class UniqueNameModel(*DefaultModelBases):
    """
    Django Model abstract base class for a basic model that has a unique name
    """
    
    name = CharField(max_length=255, unique=True, help_text="The unique name of this object")
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        abstract = True