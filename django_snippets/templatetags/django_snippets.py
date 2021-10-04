from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag()
def datelitepicker_staticfiles():
    return mark_safe('<script src="https://cdn.jsdelivr.net/npm/litepicker/dist/litepicker.js"></script>')