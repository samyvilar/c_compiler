__author__ = 'samyvilar'

import sys
from itertools import chain, izip, repeat, imap, ifilterfalse
from front_end.loader.locations import loc

from front_end.parser.ast.expressions import CommaExpression

import utils.symbol_table

from front_end.parser.ast.declarations import Declaration, name
from front_end.parser.types import c_type

from front_end.parser.declarations.declarations import declarations, external_declaration
from front_end.parser.declarations.declarators import declarator, abstract_declarator, declarator
from front_end.parser.declarations.declarators import storage_class_specifier
from front_end.parser.declarations.type_name import type_name, type_specifier, type_qualifiers, specifier_qualifier_list

from front_end.parser.expressions.binary import assignment_expression, logical_or_expression
from front_end.parser.expressions.cast import cast_expression
from front_end.parser.expressions.initializer import initializer
from front_end.parser.expressions.postfix import postfix_expression
from front_end.parser.expressions.primary import primary_expression, compound_literal
from front_end.parser.expressions.unary import unary_expression
from front_end.parser.statements.labels import labeled_statement

from front_end.parser.expressions.constant import constant_expression as _constant_expression_func
from front_end.parser.expressions.expression import expression as _expression_func
from front_end.parser.statements.compound import statement as _statement_func
from front_end.parser.declarations.declarations import translation_unit as _translation_unit_func

from loggers import logging


logger = logging.getLogger('parser')

current_module = sys.modules[__name__]


class SymbolTable(utils.symbol_table.SymbolTable):
    def __setitem__(self, key, value):
        # C allows multiple declarations, so long as long they are all consistent, with previous declarations
        # AND a single definition.
        # possible scenarios
        # 1) Giving a declaration, check its consistent with previous declaration or definition if any.
        # 2) Giving a definition, check its consistent with previous declaration and its consistent with previous
        # declaration if any.

        if isinstance(value, Declaration) and key in self:  # check declarations/definitions ...
            # either function definition, definition or declaration or constant_expression(for enums) ...
            # check for consistency.
            prev = self[key]
            if isinstance(prev, Declaration) and c_type(value) == c_type(prev) and name(value) == name(prev):
            # TODO: check storage class, extern vs static declarations/definitions ...
                # if previous is declaration pop it and insert new either def or dec
                _ = type(prev) is Declaration and self.pop(key)  # pop previous declaration otherwise do nothing ...
            else:
                raise ValueError('{l} inconsistent def/dec with previous at {a}'.format(l=loc(value), a=loc(self[key])))

        super(SymbolTable, self).__setitem__(key, value)


def get_entry_point_func(entry_point_name):
    def func(tokens, symbol_table=None, _entry_point=entry_point_name):
        if symbol_table is None:
            symbol_table = SymbolTable(default_dependencies)
        else:
            symbol_table.update(ifilterfalse(lambda item: item[0] in symbol_table, default_dependencies.iteritems()))
        return symbol_table['__ {0} __'.format(_entry_point)](tokens, symbol_table)
    return func

entry_point_names = 'constant_expression', 'expression', 'statement', 'translation_unit'
for _name in entry_point_names:
    setattr(current_module, _name, get_entry_point_func(_name))

dependency_names = \
    'declarations', \
    'external_declaration',\
    'declarator', \
    'abstract_declarator',\
    'declarator',\
    'storage_class_specifier', \
    'type_specifier', \
    'type_qualifiers', \
    'specifier_qualifier_list',\
    'assignment_expression',\
    'cast_expression',\
    'initializer',  \
    'postfix_expression',\
    'primary_expression',\
    'unary_expression',\
    'logical_or_expression',\
    'compound_literal', \
    'type_name', \
    'labeled_statement'

default_dependencies = dict(chain(
    izip(imap('__ {0} __'.format, dependency_names), imap(getattr, repeat(current_module), dependency_names)),
    izip(
        imap('__ {0} __'.format, entry_point_names),
        imap(getattr, repeat(current_module), imap('_{0}_func'.format, entry_point_names))
    )
))


def parse(tokens=(), symbol_table=None):
    return translation_unit(iter(tokens), symbol_table)