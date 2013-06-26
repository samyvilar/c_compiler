__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_statements import TestStatements


class TestPrefix(TestStatements):
    def test_increment(self):
        source = """
        {
            int a = 10;
            int b = ++a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 11)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 11)

    def test_decrement(self):
        source = """
        {
            int a = 10;
            int b = --a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 9)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 9)

    def test_address_of(self):
        source = """
        {
            int a = 10;
            int *b = &a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 10)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], self.cpu.stack_pointer)

    def test_dereference(self):
        source = """
        {
            int a = 10;
            int *b = &a;
            *b = 9;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 9)

    def test_minus(self):
        source = """
        {
            int a = 10;
            a = -a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], -10)

    def test_plus(self):
        source = """
        {
            int a = -10;
            a = +a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], -10)

    def test_not(self):
        source = """
        {
            int a = 10;
            a = !a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)

    def test_bitwise_not(self):
        source = """
        {
            int a = 10;
            a = ~a;
        }
        """
        super(TestPrefix, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], ~10)