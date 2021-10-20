from django.forms.widgets import NumberInput
from django.db.models import FloatField
from django.forms import FloatField as FloatFormField

class PrefixSuffixAdminCSSMixin:
    """
    Mixin for ModelAdmin classes that adds CSS needed for Input Prefix/Suffix (if needed)
    css is based on the example here: https://codepen.io/chamsi/pen/LavooJ
    This Mixin class is included automatically if you use `build_admin_models` in admin.py
    """
    
    class Media:
        css = {
             'all': ('css/django-snippets/prefix_suffix_widget.css',)
        }
        
class PrefixSuffixInput(NumberInput):
    """
    Input widget with prefix/suffix box displayed in admin change form
    set either/both of `widget_suffix` or `widget_prefix` as an attribute on subclasses to get a prefix to appear
    e.g.
    class MyInput(PrefixSuffixInput):
        widget_prefix = '£'
        widget_suffix = 'p'
        
    see PercentInput as an example
    """
    
    template_name = 'widgets/prefix_suffix_input.html'

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['widget']['suffix'] = getattr(self, 'widget_suffix', None)
        context['widget']['prefix'] = getattr(self, 'widget_prefix', None)
        return context
    
class PercentInput(PrefixSuffixInput):
    widget_suffix = '%'

    def format_value(self, value):
        # Return a value as it should appear when rendered in a form template (i.e. scale stored value by 100 for display)
        if value == '' or value is None:
            return None
        if isinstance(value, str):
            # values in failed django forms are str rather than float and do not need scaling
            return super().format_value(float(value))
        else:
            return super().format_value(float(value)*100)

class PercentFormField(FloatFormField):
    """
    FormField for PercentField
    """
    widget = PercentInput
    
    def to_python(self, value):
        # If the value is not already an int or float, use super().to_python to convert to a number, and then divide by 100
        if isinstance(value, (int, float)):
            return value
        else:
            pval = super().to_python(value)
            if pval is not None:
                return pval / 100.0
            else:
                return None

class PercentField(FloatField):
    """
    A FloatField that translates between percentages entered by users on the 0-100% scale that are stored on the 0-1.0 scale
    """
    
    def formfield(self, **kwargs):
        #override the formfield for this class unless specified in kwargs
        #see https://docs.djangoproject.com/en/3.0/howto/custom-model-fields/#specifying-form-field-for-model-field
        defaults = {'form_class': PercentFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)