from django.contrib import admin
from django.db.models import Model

from import_export.resources import ModelResource as ImportExportModelResource
from import_export.admin import ExportMixin

from .fields import PrefixSuffixAdminCSSMixin
from .urls import url_to_admin_changeform

class NextPreviousAdminMixin: 
    """
    Adds a Next/Previous object instance link to each Admin Change Form
    See templates/admin/change_form.html"""
    
    def render_change_form(self, request, context, obj=None, **kwargs):
        context.update({
            'admin_next_instance_href': self.get_next_or_prev_instance(obj, 'gt'),
            'admin_prev_instance_href': self.get_next_or_prev_instance(obj, 'lt'),
        })
        return super().render_change_form(request, context, obj=None, **kwargs)
    
    def get_next_or_prev_instance(self, obj, gt_or_lt):
        order_by = {'gt': 'pk', 'lt': '-pk'}[gt_or_lt]
        try:
            filter_kwargs = {'pk__' + gt_or_lt: obj.pk}
            other_obj = obj.__class__.objects.filter(**filter_kwargs).order_by(order_by)[0]
        except IndexError:
            obj_link = None
        else:
            obj_link = url_to_admin_changeform(other_obj)
        return obj_link
    
class FormattedListDisplayMixin:
    """
    Mixin to allow tuples specifying formats to be used in Admin list_display
    - this allows columns to be formatted in Admin list display,
      without a custom function for each field that needs to be formatted.
    Note that new-style .format strings should be used
    e.g.     list_display = ('id', ('amount', '{:.2f} EUR'), ('interest', '{:.2%}'))
    adapted from https://stackoverflow.com/a/41299328/1280629
    
    Included by default by `build_admin_models` function below
    """
    def __init__(self, model, *args, **kwargs):
        all_fields = process_formatted_list_display(self.list_display, model)
        self.list_display = all_fields
        super().__init__(model, *args, **kwargs)

def process_formatted_list_display(list_display, cls = None):
    """
    Transforms a list_display list with format specifiers into one with appropriate formatting functions.
    Example input: list_display = ('id', ('amount', '{:.2f} EUR'), ('interest', '{:.2%}'))
    
    If "cls" is passed, for any generated formatting function:
    - will pull the "short_description" and "admin_order_field" from the original Model Field
    - these will then be used in the Admin list for the model
    """
    def generate_formatter(name, str_format):
        def formatter_fn(obj):
            val = getattr(obj, name)
            if callable(val):
                val = val()
            if val is not None:
                return str_format.format(val)
            else:
                return None
        
        if cls is not None and callable(getattr(cls, name, None)):
            attr = getattr(cls, name, None)
            formatter_fn.short_description = getattr(attr, 'short_description', name.replace('_', ' '))
            formatter_fn.admin_order_field = getattr(attr, 'admin_order_field', name)
        else:
            formatter_fn.short_description = name.replace('_', ' ')
            formatter_fn.admin_order_field = name
        return formatter_fn

    all_fields = []
    for f in list_display:
        if isinstance(f, tuple):
            if len(f) == 2:
                formatter_fn = generate_formatter(f[0], f[1])
                all_fields.append(formatter_fn)
            else:
                raise AttributeError('Invalid value in list_display: %s' % str(f))
        else:
            all_fields.append(f)
    return all_fields

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

def build_admin_models(models_list, extra_mixins = {}, default_base_admin_cls = admin.ModelAdmin):
    """
    Automates the process of building ModelAdmin classes with a default set of base classes.
    An optional AdminMixin nested class can be placed on each Model 
    - this will be used as an additional Mixin for the Admin class for that Model
    - this allows ModelAdmin customisation to be done from the model itself...

    returns `admin_models_dict` which can be used later to get a specific Admin model if ever needed
    e.g. MyModelAdmin = admin_models_dict[MyModel]
    """
    admin_models_dict = {}   

    for ModelCls in models_list:
        #needed for Excel export via django_import_export
        class ExcelResource(ImportExportModelResource):
            class Meta:
                model = ModelCls

        admin_bases = [ExportMixin]

        #look for "AdminMixin" on the ModelCls and its base classes, and if present use it as a base class for the ModelAdminCls
        #this allows us to specify all the Admin stuff on ModelCls, rather than repeating everything and splitting it
        #onto a custom ModelAdminCls
        for BaseModelCls in ModelCls.__bases__ + (ModelCls,):
            admin_mixin = getattr(BaseModelCls, 'AdminMixin', extra_mixins.get(BaseModelCls, None))
            if admin_mixin is not None and admin_mixin not in admin_bases:
                admin_bases.append(admin_mixin)

        admin_bases.extend([FormattedListDisplayMixin, PrefixSuffixAdminCSSMixin, NextPreviousAdminMixin, default_base_admin_cls])
        class ModelAdminCls(*admin_bases):
            resource_class = ExcelResource

        admin.site.register(ModelCls, ModelAdminCls)

        admin_models_dict[ModelCls] = ModelAdminCls
        ModelCls.ModelAdminCls = ModelAdminCls
            
    return admin_models_dict
                
                

