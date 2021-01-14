from django.db.models import Model, Manager, ForeignKey, CharField, DateTimeField, CASCADE, DO_NOTHING
from django.conf import settings

class DataConsistencyError(RuntimeError): pass

def instance_to_dict(instance):
    # see https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields:
        data[f.name] = getattr(instance, f.name)
    return data

def get_nk_fields(model_or_instance):
    if hasattr(model_or_instance, 'get_natural_key_fields'):
        return model_or_instance.get_natural_key_fields()
    else:
        model_cls = model_or_instance if isinstance(model_or_instance, type) else model_or_instance.__class__
        raise ValueError('Model "%s" does not provide a get_natural_key_fields() method'
                         % model_cls.__name__)
    
def get_package_models(models_package, model_filter_fn = None, include_abstract = False):
    """Return all the Django Models present in a particular module"""
    models_list = []
    for k, obj in models_package.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, Model) and obj.__module__ == models_package.__name__:
            ModelCls = obj
            if not ModelCls._meta.abstract or include_abstract:
                if model_filter_fn is None or model_filter_fn(ModelCls):
                    models_list.append(ModelCls)
                    
    return models_list

class GetOrCreateWChecksManager(Manager):
    "Manager class that provides `get_or_create_with_checks()`"
        
    def get_or_create_with_checks(self, non_key_values = {}, skip_checks = [], instance = None, key_fields = None, **key):
        """Same as `Model.objects.get_or_create()`, but also checks if `non_key_values` match those in the database if the object already exists.  
        
Either i) 'non_key_values' and **key, or ii) 'instance' and 'key_fields' should be provided
(though 'key_fields' can be omitted if the underlying Model implements 'get_natural_key_fields')."""
        if instance is not None:
            inst_dict = instance_to_dict(instance)
            if key_fields:
                key = {k: inst_dict[k] for k in key_fields}
            else:
                key = {k: inst_dict[k] for k in get_nk_fields(instance)}
            non_key_values = {k: inst_dict[k]
                              for k in inst_dict
                              if k not in key and k not in ['_foreign_key_cache', '_state']}
            
            skip_checks.append(instance._meta.pk.name)
            
        existing, created = self.get_or_create(**key, defaults = non_key_values)
        if not created:
            different_fields = {}
            for k, v in non_key_values.items():
                if k not in skip_checks:
                    existing_v = getattr(existing, k)
                    if v != existing_v:
                        different_fields[k] = (v, existing_v)

            if different_fields:
                raise DataConsistencyError('New row for {:} with key {:} differs from data in database on fields:\n{:}'
                                           .format(self.model.__name__, str(key), str(different_fields)))

        return existing, created
    
    def get_by_natural_key(self, *args):
        return self.get(**dict(zip(get_nk_fields(self.model), args)))
            
    def get_or_create_by_natural_key(self, *args):
        return self.get_or_create(**dict(zip(get_nk_fields(self.model), args)))
            
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

    def natural_key(self):
        return (self.name,)
    
    @classmethod
    def get_natural_key_fields(self):
        return ('name',)
    
    class Meta:
        ordering = ('name',)
        abstract = True