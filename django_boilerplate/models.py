from django.db.models import Model, ForeignKey, CharField, DateTimeField, CASCADE, DO_NOTHING
from django.conf import settings

#use ForeignKey_CD rather than ForeignKey directly to make all foreign keys cascade delete.  
def ForeignKey_CD(*args, **kwargs):
    return ForeignKey(*args, on_delete = CASCADE, **kwargs)

class NextPreviousMixin(object):
    def _get_next_or_prev(self, gt_or_lt):
        cached_field = '_cachednext_or_prev_' + gt_or_lt
        order_by = {'gt': 'pk', 'lt': '-pk'}[gt_or_lt]
        try:
            return getattr(self, cached_field)
        except AttributeError:
            try:
                filter_kwargs = {'pk__' + gt_or_lt: self.pk}
                setattr(self, cached_field, self.__class__.objects.filter(**filter_kwargs).order_by(order_by)[0])
            except IndexError:
                setattr(self, cached_field, None)
        return getattr(self, cached_field)   

    def admin_get_next(self):
        return self._get_next_or_prev('gt')
    
    def admin_get_previous(self):
        return self._get_next_or_prev('lt')
    
class AtLeastOneNotNullMixin(object):
    """Mixin class that overrides default django form "clean" method to ensure that at least one of several fields is not NULL (or False)
    
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
DefaultModelBases = (Model, NextPreviousMixin)

class UniqueNameModel(*DefaultModelBases):
    #template for a basic model that has a name
    name = CharField(max_length=255, unique=True, help_text="The unique name of this object")
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        abstract = True