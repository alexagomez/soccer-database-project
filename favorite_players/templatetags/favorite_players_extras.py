from django import template

register = template.Library()

@register.simple_tag
def dict_get(dct, key1):
    try:
        if dct.get(key1) is None:
            return ""
        return dct.get(key1, "")
    except AttributeError:
        return ""