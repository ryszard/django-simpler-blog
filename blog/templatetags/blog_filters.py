from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Usage:

    {{ width|multiply:12 }}

    """
    return int(value) * int(arg)
