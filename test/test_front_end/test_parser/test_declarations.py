__author__ = 'samyvilar'

from unittest import TestCase
from itertools import izip

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

from front_end.parser.ast.declarations import Declaration, Definition, AbstractDeclarator, Extern
from front_end.parser.ast.expressions import ConstantExpression
from front_end.parser.types import IntegerType, VoidType, PointerType, ArrayType, FunctionType
from front_end.parser.declarations.declarations import translation_unit


class TestDeclarations(TestCase):
    def test_simple_declarations(self):
        code = """
            int foo(int (*)(void *, int[1]));
            int a, b = 1, c = 5 + 5;
        """
        decs = translation_unit(preprocess(tokenize(source(code))))

        int_type = IntegerType('')
        exp_decls = [
            Declaration(
                'foo',
                FunctionType(int_type, [AbstractDeclarator(PointerType(FunctionType(
                    int_type,
                    [
                        AbstractDeclarator(PointerType(VoidType(''), ''), ''),
                        AbstractDeclarator(ArrayType(int_type, 1, ''), ''),
                    ],
                    '',
                ), ''), '')], ''),
                '',
            ),
            Declaration('a', int_type, ''),
            Definition('b', int_type, ConstantExpression(1, int_type, ''), '', None),
            Definition('c', int_type, ConstantExpression(10, int_type, ''), '', None)
        ]

        for got_dec, exp_dec in izip(decs, exp_decls):
            self.assertEqual(got_dec, exp_dec)