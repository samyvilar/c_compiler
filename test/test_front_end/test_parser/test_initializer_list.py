__author__ = 'samyvilar'

from unittest import TestCase
from itertools import imap

from front_end.parser.ast.expressions import exp, ConstantExpression, EmptyExpression
from front_end.parser.types import integer_type, void_pointer_type, char_type

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess
from front_end.parser.parse import parse


class TestInitializerList(TestCase):
    def test_basic_type_initializer(self):
        code = "int b = {1};"
        expr = exp(next(parse(preprocess(tokenize(source(code))))).initialization)
        self.assertEqual(ConstantExpression(1, integer_type), expr[0])

    def test_default_basic_type_initializer(self):
        code = "int b = {};"
        expr = exp(next(parse(preprocess(tokenize(source(code))))).initialization)
        self.assertEqual(EmptyExpression(integer_type), expr[0])

    def test_composite_initializer(self):
        code = """
        struct {int a[100]; struct {int b; void *ptr; char sub[10];} values[10];} g = {
            .values[0] = {-1, (void *)-1},
            .a[0 ... 99] = 1,
            .values[1 ... 5] = {.b = 5},
            .values[6 ... 9].ptr = 1,
            .values[1].sub = {1},
            .values[1].sub[0] = 'a'
        };
        """
        expr = exp(next(parse(preprocess(tokenize(source(code))))).initialization)
        a = expr[0]
        values = expr[1]

        self.assertEqual(len(a), 100)
        self.assertEqual(len(values), 10)

        a_expr = ConstantExpression(1, integer_type)
        for e in imap(lambda e: e[0], a):
            self.assertEqual(e, a_expr)

        self.assertEqual(values[0][0][0], ConstantExpression(-1, integer_type))
        self.assertEqual(values[0][1][0], ConstantExpression(-1, void_pointer_type))

        b_expr = ConstantExpression(5, integer_type)
        for index in xrange(1, 6):
            self.assertEqual(values[index][0][0], b_expr)
            self.assertEqual(values[index][1][0], EmptyExpression(integer_type))

        ptr_expr = ConstantExpression(1, void_pointer_type)
        for index in xrange(6, 10):
            self.assertEqual(values[index][1][0], ptr_expr)
            self.assertEqual(values[index][0][0], EmptyExpression(void_pointer_type))

        self.assertEqual(values[1][2][0][0], ConstantExpression(ord('a'), char_type))
