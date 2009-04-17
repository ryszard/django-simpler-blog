"""
Tests for templatetags:

>>> template.compile_string('{% load comments_extras %}{% get_recent_comments 5 as foo %}', {})
[<django.template.defaulttags.LoadNode object at ...>, <django.templatetags.comments_extras.GetRecentCommentsNode object at ...>]

"""

from django import template
from django import templatetags
