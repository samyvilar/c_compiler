__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements


class TestSelectionStatements(TestStatements):
    def test_if_statement(self):
        source = """
        {
            int a = 10;
            if (1)
                a = 0;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)

    def test_else_statement(self):
        source = """
        {
            int a = 10;
            if (0)
                a = 1;
            else
                a = 0;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 0)

    def test_else_if_statement(self):
        source = """
        {
            int a = 11;
            if (0)
                ;
            else if (1)
                a = 1;
            else
                a = 0;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_switch_statement(self):
        source = """
        {
            int a = 10, sum = 0;
            switch (10)
            {
                case 0:
                    sum = -1;
                case 1:
                    sum += 1;
                    break;
                case 10:
                    sum += 10;
                case 11:
                    {
                        sum += 1;
                        case 15:
                            sum += 1;
                    }
                    break;
                case 12:
                    sum += 1;
                default:
                    sum += 1;
            }

        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 12)

    def test_switch_statement_declarations(self):
        code = """
        {
            int sum = 0, stack_frag = 0;
            void *stack_ptr = &stack_ptr - 1;
            int temp;
            switch (0)
            {
                int a;
                case 0:
                    a = 10;
                    sum += 1;
                    int b = 10;
                case 20:
                    sum += a;
                    int c = 24;
                case 4:
                    {
                        int _ter[10] = {[0 ... 9] = -1};
                        case 10:
                            sum += b + c;
                            int d = 49;
                            void *curr = &curr - 1;
                            if (((void *)stack_ptr - (void *)curr) != 15 * sizeof(int) + sizeof(void *))
                                sum = -1;
                    }
                    void *curr = &curr - 1;
                    if ((stack_ptr - curr) != 4 * sizeof(int) + sizeof(void *))
                        sum = (stack_ptr - curr);
                    break ;
                    int u = 124;
                    sum += u + a;
                    break ;

                default:
                    sum = -1;
            }
            int g = -1;
            if ((stack_ptr - ((void *)&g - 1)) != 2 * sizeof(int))
                sum = -1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 45)

