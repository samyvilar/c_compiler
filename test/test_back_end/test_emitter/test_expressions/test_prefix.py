__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements
from front_end.parser.ast.expressions import ConstantExpression
from front_end.parser.types import IntegerType


class TestPrefix(TestStatements):
    def test_increment(self):
        source = """
        {
            int a = 10;
            int b = ++a;
            a = a - b;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))

    def test_decrement(self):
        source = """
        {
            int a = 10;
            int b = --a;
            a = a - b;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))

    def test_address_of(self):
        source = """
        {
            int a = 10;
            int *b = &a;
            a = (unsigned long long)&a - (unsigned long long)b;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))

    def test_dereference(self):
        source = """
        {
            int a = 10;
            int *b = &a;
            *b = 9;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(9, IntegerType()))

    def test_minus(self):
        source = """
        {
            int a = -10;
            a = -a;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))

    def test_plus(self):
        source = """
        {
            int a = 10;
            a = +a;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))

    def test_not(self):
        source = """
        {
            int a = 10;
            a = !a;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))

    def test_bitwise_not(self):
        source = """
        {
            int a = -10;
            a = ~a;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(9, IntegerType()))