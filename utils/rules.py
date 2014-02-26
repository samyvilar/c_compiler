__author__ = 'samyvilar'

from itertools import ifilter, repeat, imap
from collections import defaultdict

from front_end.loader.locations import loc
from utils import get_attribute_func

rules = get_attribute_func('rules')


def identity(value):
    return value

no_default = object()


def get_rule(obj, key, default=no_default, hash_funcs=(identity,)):
    hash_value = next(ifilter(rules(obj).__contains__, imap(apply, hash_funcs, repeat((key,)))), key)
    try:
        return rules(obj)[hash_value] if default is no_default else rules(obj).get(hash_value, default)
    except KeyError as er:
        raise KeyError('{l} No rule with key {k} for {o} using funcs {f}'.format(
            l=loc(key), k=key, o=obj, f=hash_funcs
        ))


def set_rules(obj, rules, default=no_default):
    if isinstance(rules, set):
        _rules = rules
    elif default is not no_default:
        _rules = defaultdict(lambda: default, rules)
    else:
        _rules = dict(rules)
    obj.rules = _rules


