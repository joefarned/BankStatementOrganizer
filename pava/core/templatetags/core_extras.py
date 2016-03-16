from django import template
register = template.Library()

@register.filter
def get(mapping, key):
  return mapping.get(key, '')

@register.filter
def negate(value):
    if value > 0:
        return 0 - value
    else:
        return '+' + str(0 - value)
