from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    """
    Get dictionary value from key
    @param dictionary  The dictionary
    @param key  The key
    @returns  The value
    """
    return dictionary.get(key)
