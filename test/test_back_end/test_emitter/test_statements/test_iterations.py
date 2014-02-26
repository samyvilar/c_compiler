__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements
from front_end.parser.ast.expressions import ConstantExpression, IntegerType


class TestWhile(TestStatements):
    def test_false_while_loop(self):
        source = """
        {
            int sum = 0;
            while (0)
                sum += 1;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))

    def test_true_while_loop(self):
        source = """
        {
            int sum = 0, index = 10;
            while (sum < index)
                sum += 1;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))

    def test_compound_while_loop(self):
        source = """
        {
            int sum = 10, index = 0;
            while (index < 10)
            {
                int sum1 = 0;
                index += 1;
                sum1 = index;
            }
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
        # self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 10)


class TestDoWhile(TestStatements):
    def test_false_do_while_loop(self):
        source = """
        {
            int sum = 0;
            do
                sum = 10;
            while (0);
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
        # self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 10)

    def test_true_do_while_loop(self):
        source = """
        {
            int sum = 0, index = 10;
            do
                sum += 1;
            while(sum < index);
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
        # self.assertEqual(self.mem[self.cpu.stack_pointer], 10)

    def test_compound_do_while_loop(self):
        source = """
        {
            int sum = 0, index = 10;
            do
            {
                sum += 1;
            } while (sum < index);
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
        # self.assertEqual(self.mem[self.cpu.stack_pointer], 10)


class TestFor(TestStatements):
    def test_false_for_loop(self):
        source = """
        {
            int index;
            for (index = 10; 0; index += 1)
                index = 0;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
        # self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 10)

    def test_true_for_loop(self):
        source = """
        {
            int index;
            for (index = 0; index < 10; index += 1);
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
        # self.assertEqual(self.mem[self.cpu.stack_pointer], 10)

    def test_compound_for_loop(self):
        source = """
        {
            int index = 10;
            for (; index; )
            {
                int sum = 10;
                index -= 1;
            }
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))
        # self.assertEqual(self.mem[self.cpu.stack_pointer], 0)
