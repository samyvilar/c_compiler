__author__ = 'samyvilar'

from unittest import TestCase

from front_end.loader.locations import LocationNotSet
from front_end.tokenizer.tokenize import Tokenize
from front_end.parser.ast.declarations import Declaration, Definition, AbstractDeclarator
from front_end.parser.ast.expressions import ConstantExpression
from front_end.parser.types import IntegerType, VoidType, PointerType, ArrayType, FunctionType
from front_end.parser.declarations.declarations import translation_unit
from front_end.parser.symbol_table import SymbolTable


class TestDeclarations(TestCase):
    def test_simple_declarations(self):
        source = """
int foo(int (*)(void *, int[1]));
int a, b = 1, c = 5 + 5;
"""
        tokens = Tokenize(source)
        symbol_table = SymbolTable()
        decs = translation_unit(tokens, symbol_table)

        int_type = IntegerType(LocationNotSet)
        decls = [
            Declaration(
                'foo',
                FunctionType(
                    int_type,
                    [
                        AbstractDeclarator(
                            PointerType(
                                FunctionType(
                                    int_type,
                                    [
                                        AbstractDeclarator(
                                            PointerType(VoidType(LocationNotSet), LocationNotSet),
                                            LocationNotSet),
                                        AbstractDeclarator(ArrayType(int_type, 1, LocationNotSet), LocationNotSet),
                                    ],
                                    LocationNotSet,
                                ),
                                LocationNotSet,
                            ),
                            LocationNotSet,
                        ),
                    ],
                    LocationNotSet,
                ),
                LocationNotSet,
            ),
            Declaration('a', int_type, LocationNotSet),
            Definition('b', int_type, ConstantExpression(1, int_type, LocationNotSet), LocationNotSet, None),
            Definition('c', int_type, ConstantExpression(10, int_type, LocationNotSet), LocationNotSet, None)
        ]

        for index, dec in enumerate(decs):
            self.assertEqual(dec, decls[index])

