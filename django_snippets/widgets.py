from django.forms import widgets

# ReadOnlyValueWidget and ReadOnlyFKWidget
# Based on the below answer on the SO question:
# "In a Django form, how do I make a field readonly (or disabled) so that it cannot be edited?""
# https://stackoverflow.com/a/15134622/4126114
# and this gist:
# https://gist.github.com/shadiakiki1986/e27edd06f2cb3ad4110405235849ebfb
#
# Usage of either widget classes below:
# class MyForm(forms.ModelForm):
#  #n.b. ReadOnly fields should be marked disabled so that their values are ignored/replaced with "initial" during form processing
#  field = forms.XXXField(disabled = True, widget = ReadOnlyValueWidget()) 
#  foreign_key = forms.ModelChoiceField(..., disabled = True, widget = ReadOnlyFKWidget((fk_to_model = DestModel)) 


# For non-foreign-key fields, display them in <p>...</p>
# Note the "str(...)" necessary for things like datetime objects
# Also, without the <p>...</p>, the field in bootstrap_form does not show up aligned properly
class ReadOnlyValueWidget(widgets.Widget):
    def __init__(self, string_format_fn = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.string_format_fn = string_format_fn
        
    def render(self, name, value, attrs=None, renderer=None):
        if self.string_format_fn:
            str_val = self.string_format_fn(value)
        else:
            str_val = str(value)
        return "<p>%s</p>" % str_val

# For foreign-key fields, display their __str()__ result
# the model that is linked ot by the FK must be passed as fk_to_model
class ReadOnlyFKWidget(widgets.Widget):
    def __init__(self, fk_to_model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fk_to_model = fk_to_model

    def render(self, _, value, attrs=None):
        instance = self.fk_to_model.objects.get(pk = value)
        return "<p>%s</p>" % str(instance)