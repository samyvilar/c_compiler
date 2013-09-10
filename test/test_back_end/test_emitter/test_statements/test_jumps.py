__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements


class TestJump(TestStatements):
    def test_continue(self):
        source = """
        {
            int sum = 0, index = 0;
            while (index < 10)
            {
                index += 1;
                continue ;
                sum += 1;
            }
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)

    def test_break(self):
        source = """
        {
            int sum = 0, index = 0;
            while (index < 10)
            {
                sum += 1;
                break ;
            }
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_nested_continue(self):
        source = """
        {
            int sum = 0, index = 0;
            for (; index < 100; index += 1)
            {
                for (index = 0; index < 10; index += 1)
                {
                    continue ;
                    sum += 1;
                }
                break ;
            }
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 10)


class TestGoto(TestStatements):
    def test_goto(self):
        source = """
        {
            goto label;
            int index = 10;
            label:
                index = 1;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_goto_into_nested(self):
        source = """
        {
            goto label;
            int index1 = 10, index2 = 11;
            index2 = 1;
            {
                int index = 10;
                {
                    label:
                        index1 = 0;
                }
            }
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)

    def test_goto_out_of_nested(self):
        source = """
        {
            int index;
            {
                int index1, index0;
                {
                    int index3;
                    goto label;
                }
            }
            int foo;
            label:
            foo = 1;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 1)