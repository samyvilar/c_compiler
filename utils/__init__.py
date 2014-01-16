__author__ = 'samyvilar'

__required__ = object()


def get_attribute_func(attribute_name):
    def func(obj, default=__required__, attribute_name=attribute_name):
        return getattr(obj, attribute_name) if default is __required__ else getattr(obj, attribute_name, default)
    return func

