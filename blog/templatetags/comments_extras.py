from django import template
from utils import get_x_as_y_tag
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.models import Comment
from django.db.models import get_model

register = template.Library()

class GetRecentCommentsNode(template.Node):
    def __init__(self, model_name, number, var_name):
        self.number = number
        self.model_name = model_name
        self.var_name = var_name
    def render(self, context):
        ctype = ContentType.objects.get_for_model(get_model(*self.model_name.split('.')))
        context[self.var_name] = Comment.objects.filter(content_type=ctype, is_public=True).order_by('-submit_date').all()[:self.number]
        return ''



@register.tag(name='get_recent_comments')
@get_x_as_y_tag
def get_recent_comments(args, var_name):
    """Usage in a template:
    {% load comment_extras %}
    {% get_recent_comments blog.entry, 10 as recent_comments %}

    >>> template.compile_string('{% load comments_extra %} {% get_recent_comments 5 as foo %}', {})

    [<django.template.defaulttags.LoadNode object at 0x11c9370>,
    <Text Node: ' '>,
    <django.templatetags.comments_extra.GetRecentCommentsNode object at ...>]

    >>> 1
    0
    """
    # This version uses a regular expression to parse tag contents.
    try:
        model_name, number = [a.strip() for a in args.split(',')]
        number = int(number)
    except ValueError:
        raise template.TemplateSyntaxError, "Wrong arguments given to tag get_recent_comments."
    return GetRecentCommentsNode(model_name, number, var_name)
