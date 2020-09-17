"""
Provides a template Model class "EnumModel" that can be used to tersely specify Models with a smaller number of instances, e.g.

class PizzaBase(UniqueNameModel, EnumModel): 
    class EnumInstances:
        WHITE = 'No tomato'
        RED = 'No cheese'
        STANDARD = 'Tomato+Cheese'
        
"""

from django.db.models.base import ModelBase
from django.db.models import Model

from django.utils.functional import classproperty
from functools import partial

from django_snippets.models import get_nk_fields
from django_snippets.admin import get_package_models

def _enum_cached_get_fn(cls, instance_name, key, *args, **kwargs):
    """Fetch a model instance from the DB, and store it on cls as instance_name.
Assuming cls.instance_name is initially _enum_cached_get_fn, this will replace _enum_cached_get_fn with the actual instance"""
    try:
        db_instance = cls.objects.get(**key)
    except cls.DoesNotExist as ex:
        raise cls.DoesNotExist('Cannot get instance %s of EnumModel %s - it does not exist'
                               % (instance_name, str(cls))) from ex
    except cls.MultipleObjectsReturned as ex:
        raise cls.MultipleObjectsReturned('Multiple instances matching query for %s of EnumModel %s exist'
                               % (instance_name, str(cls))) from ex
    else:
        setattr(cls, instance_name, db_instance)
        return db_instance

class EnumModelMetaclass(ModelBase): #n.b. needs to inherit from ModelBase so that Model subclasses same the same metaclass parent
    def __new__(cls, name, bases, attrs):
        cls = ModelBase.__new__(cls, name, bases, attrs)

        instances_added = False
        for instance_name, key in cls.get_enum_instances_map().items():
            get_fn = classproperty(
                partial(_enum_cached_get_fn, 
                        instance_name = instance_name,
                        key = key)
            )

            setattr(cls, instance_name, get_fn)
            instances_added = True
                
        #if instances_added:
        #    from django.db.models.signals import post_migrate
        #    post_migrate.connect(cls.insert_enum_instances)
        return cls
    
class EnumModel(Model, metaclass = EnumModelMetaclass): 
    """Mixin Base Class that provides cached attributes on a Model class for each instance in EnumInstances.

Example usage:

```
class PizzaBase(UniqueNameModel, EnumModel): 
    class EnumInstances:
        WHITE = 'No tomato'
        RED = 'No cheese'
        STANDARD = 'Tomato+Cheese'
```

Later in e.g. views you can access `PizzaBase.WHITE` which will return the corresponding PizzaBase instance
"""
    
    @classmethod
    def get_enum_instances_map(cls):
        result = {}
        if cls.__name__ != 'EnumModel':
            try:
                instances_cls = cls.EnumInstances
            except AttributeError as ex:
                import warnings
                warnings.warn('Enum Models require an EnumInstances attribute which is not provided for on %s' % str(cls))
                return {}

            for instance_name, instance_key in vars(instances_cls).items():
                if not instance_name.startswith('__'):
                    if isinstance(instance_key, dict):
                        key = instance_key
                    else:
                        if isinstance(instance_key, (list, tuple)):
                            key_args = instance_key
                        else:
                            key_args = (instance_key,)
                        key = dict(zip(get_nk_fields(cls), key_args))

                    result[instance_name] = key
        return result
    
    @classmethod
    def insert_enum_instances(cls, *args, **kwargs):
        created_count = 0
        if cls.objects.count() == 0:
            for instance_name, key in cls.get_enum_instances_map().items():
                inst, created = cls.objects.get_or_create(**key)
                created_count += created
        return created_count

    @staticmethod
    def create_package_model_instances(package):
        "Create all the DB instances of EnumModel classes in the given package (module)"
        created_count = 0
        for model_cls in get_package_models(package):
            if issubclass(model_cls, EnumModel):
                created_count += model_cls.insert_enum_instances()

        return created_count
    
    class Meta:
        abstract = True
