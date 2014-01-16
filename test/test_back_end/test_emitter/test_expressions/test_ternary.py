__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements
from front_end.parser.ast.expressions import ConstantExpression, IntegerType


class TestTernary(TestStatements):
    def test_ternary(self):
        code = '''
        {
            int b = 11;
            int foo = b ? b += 2 : (foo += 3);
            b = b - foo;
        }
        '''
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(0, IntegerType()))

    def test_ternary_false(self):
        code = '''
        {
            int b = 0;
            int c = 1;
            int foo = b ? c += 1 : b;
            b = b + c + foo;
        }
        '''
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(1, IntegerType()))