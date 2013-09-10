__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib


class TestExit(TestStdLib):
    def test_exit(self):
        code = """
        #include <stdlib.h>

        int main()
        {
            exit(0);
            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)

    def test_exit_nested(self):
        code = """
        #include <stdlib.h>

        int foo_2(int value)
        {
            exit(value);
        }

        void foo(int value)
        {
            if (value < 100)
                foo(value + 1);
            else
                foo_2(value);
        }

        int main()
        {
            foo(0);
            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 100)

