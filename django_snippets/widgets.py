from __future__ import annotations

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


class DateLitepickerInput(widgets.DateInput):
    template_name = 'widgets/date_litepicker.html'

    def __init__(self, enabled_dates: Optional[list[datetime.date]] = None,
                       form_submit_on_select = False,
                       max_date: Optional[datetime.date] = None,
                       min_date: Optional[datetime.date] = None,
                       date_format: str = '%Y-%m-%d',
                       *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enabled_dates = enabled_dates
        self.form_submit_on_select = form_submit_on_select
        self.max_date = max_date
        self.min_date = min_date
        self.date_format = date_format

    def date_to_str(self, dateval):
        return dateval.strftime(self.date_format)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['enabled_dates'] = str([self.date_to_str(d) for d in self.enabled_dates])
        context['form_submit_on_select'] = self.form_submit_on_select
        max_date = (self.max_date
                    if self.max_date is not None
                    else max(self.enabled_dates)
                         if self.enabled_dates
                         else None)
        context['max_date'] = self.date_to_str(max_date) if max_date is not None else None
        min_date = (self.min_date
                    if self.min_date is not None
                    else min(self.enabled_dates)
                         if self.enabled_dates
                         else None)
        context['min_date'] = self.date_to_str(min_date) if min_date is not None else None
        return context

class ToggleSwitchInput(widgets.CheckboxInput):
    template_name = 'widgets/toggle-switch.html'

    class Media:
        css = {
             'all': ('css/django-snippets/toggle-switch.css',)
        }

    def __init__(self,
                 *args,
                 prefix_label: str = None,
                 suffix_label: str = None,
                 off_color = "#478866",
                 on_color = "#444488",
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.off_color = off_color
        self.on_color = on_color
        self.prefix_label = prefix_label
        self.suffix_label = suffix_label

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['widget'].update({
            'off_color': self.off_color,
            'on_color': self.on_color,
            'prefix_label': self.prefix_label,
            'suffix_label': self.suffix_label,
        })
        return context