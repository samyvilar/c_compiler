__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements


class TestTernary(TestStatements):
    def test_ternary(self):
        code = '''
        {
            int b = 11;
            int foo = b ? b += 2 : (foo += 3);
        }
        '''
        super(TestTernary, self).evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 13)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 13)

    def test_ternary_false(self):
        code = '''
        {
            int b = 0;
            int c = 1;
            int foo = b ? c += 1 : b;
        }
        '''
        super(TestTernary, self).evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 1)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 2], 0)