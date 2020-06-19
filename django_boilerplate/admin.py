from django.contrib import admin
from django.db.models import Model
from simple_history.admin import SimpleHistoryAdmin

from import_export.resources import ModelResource as ImportExportModelResource

from import_export.admin import ExportMixin
from modelclone import ClonableModelAdmin

from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter

from .fields import PrefixSuffixAdminCSSMixin

def process_formatted_list_display(list_display, cls = None):
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


# Mixin to allow tuples specifying formats to be used in list_display
# note that new-style .format strings should be used
# e.g.     list_display = ('id', ('amount', '{:.2f} EUR'), ('interest', '{:.2%}'))
# adapted from https://stackoverflow.com/a/41299328/1280629
class FormattedListDisplayMixin:
    """Handles column formatting in list display"""
    def __init__(self, model, *args, **kwargs):
        all_fields = process_formatted_list_display(self.list_display, model)
        self.list_display = all_fields
        super().__init__(model, *args, **kwargs)

#building ModelAdmin classes is repetitive, tedious and quickly becomes difficult to maintain
#I've automated the process of building them here

def build_admin_models(models_package):
    #admin_models_dict can be used later to get a specific Admin model if ever needed
    #e.g. admin_models_dict[SecuritisationNote]
    admin_models_dict = {}   

    for k, obj in models_package.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, Model) and obj.__module__ == models_package.__name__:
            ModelCls = obj
            if not ModelCls._meta.abstract and not ModelCls.__name__.startswith('Historical'):

                #needed for Excel export via django_import_export
                class ExcelResource(ImportExportModelResource):
                    class Meta:
                        model = ModelCls

                admin_bases = [ExportMixin]

                #look for "AdminMixin" on the ModelCls and its base classes, and if present use it as a base class for the ModelAdminCls
                #this allows us to specify all the Admin stuff on ModelCls, rather than repeating everything and splitting it
                #onto a custom ModelAdminCls
                for BaseModelCls in ModelCls.__bases__ + (ModelCls,):
                    admin_mixin = getattr(BaseModelCls, 'AdminMixin', None)
                    if admin_mixin is not None:
                        admin_bases.append(admin_mixin)

                admin_bases.extend([FormattedListDisplayMixin, PrefixSuffixAdminCSSMixin])

                #if ModelCls is abs_data_models.SecuritisationNote:
                #    admin_bases.append(ClonableModelAdmin)

                admin_bases.append(SimpleHistoryAdmin)
                class ModelAdminCls(*admin_bases):
                    resource_class = ExcelResource

                admin.site.register(ModelCls, ModelAdminCls)

                admin_models_dict[ModelCls] = ModelAdminCls
                ModelCls.ModelAdminCls = ModelAdminCls
            
    return admin_models_dict
                
                

