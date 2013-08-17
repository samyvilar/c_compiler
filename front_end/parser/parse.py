__author__ = 'samyvilar'

from front_end.parser.declarations.declarations import translation_unit


def parse(tokens=(), symbol_table=None):
    return translation_unit(iter(tokens), symbol_table)