from django import template
import re


def get_x_as_y_tag(fun):
    """Make a tag with the syntax:

    {% foo some_argument as some_var_name %}

    The decorated function should take two arguments: an argument
    (which wil be passed as a string) and a name of the context
    variable. It should return a template.Node object.
    """
    def wrapper(parser, token):
        try:
            # Splitting by None == splitting by spaces.
            tag_name, arg = token.contents.split(None, 1)
        except ValueError:
            raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
        m = re.search(r'(.+) as (\w+)', arg)
        if not m:
            raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
        argument, var_name = m.groups()
        return fun(argument, var_name)

    return wrapper
