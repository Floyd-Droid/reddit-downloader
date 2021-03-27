from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='add_spaces')
@stringfilter
def add_spaces(value):
    return value.replace(',', ', ')


# register.filter('add_spaces', add_spaces)