from django import template
import re

from utils import get_x_as_y_tag
from blog.models import Category


register = template.Library()

class GetCategoryNode(template.Node):
    def __init__(self, name, var_name):
        self.name = name
        self.var_name = var_name
    def render(self, context):
        context[self.var_name] = Category.objects.get(name=self.name)
        return ''

@register.tag(name='get_category')
@get_x_as_y_tag
def get_category(name, var_name):
    """Usage in a template:
    {% load category_extras %}
    {% get_category "some category" as some_category %}
    """
    if not (name[0] == name[-1] and name[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    return GetCategoryNode(name[1:-1], var_name)
