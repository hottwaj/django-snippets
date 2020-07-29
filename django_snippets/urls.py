from django.urls import reverse

def url_to_admin_changeform(object_instance):
    """
    Returns the admin URL for a given Model object instance.
    Adapted from: https://stackoverflow.com/a/1720961
    """
    return reverse('admin:%s_%s_change' 
                   % (object_instance._meta.app_label,  object_instance._meta.model_name), args=(object_instance.pk,))