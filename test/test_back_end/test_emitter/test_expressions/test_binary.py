__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements


class TestCompoundAssignment(TestStatements):
    def test_compound_addition(self):
        code = """
        {
            int a = 10, b = 1;
            a += b;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 11)
