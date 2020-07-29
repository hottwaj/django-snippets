from django.forms import BaseModelFormSet

class BaseModelFormSetKeepInitial(BaseModelFormSet):
    """
    For some reason Django ModelFormSet removes "extra" fields (non model fields) in a formset "initial" list.  
    This BaseModelFormSet overrides that behaviour.
    See https://stackoverflow.com/questions/34162080/how-do-i-set-initial-values-for-extra-fields-on-a-django-model-formset
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial = kwargs['initial']