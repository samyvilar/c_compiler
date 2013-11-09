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
            a = sum;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 12)

    def test_switch_statement_declarations(self):
        code = """
        {
            int sum = 0, a = -10;
            int temp;
            switch ((char)0)
            {
                int a;
                case (char)0:
                    a = 10;
                    sum += 1;
                    int b = 11;
                case (char)20:
                    sum += a;
                    int c = 24;
                case (char)4:
                    {
                        int _ter[10] = {[0 ... 9] = -1};
                        case (char)10:
                            sum += b + c;
                            int d = 50;
                            if (a != 10 || b != 11 || d != 50 || sum != 46 ||
                                _ter[0] != -1 || _ter[1] != -1 || _ter[2] != -1 || _ter[3] != -1 || _ter[4] != -1 ||
                                _ter[5] != -1 || _ter[6] != -1 || _ter[7] != -1 || _ter[8] != -1 || _ter[9] != -1)
                                sum = -1;
                    }
                    break ;
                    int u = 124;
                    sum += u + a;
                    break ;

                default:
                    sum = -1;
            }
            int g = -1;

            if (sum != 46 || a != -10 || g != -1)
                sum = -1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 46)

    def test_nested_switch_statement(self):
        code = """
        {
            int value = 0;
            switch (0) {
                case 0:
                    switch (11) {
                        case 11:
                            value = 10;
                            break ;
                    }
                    value--;
                    break ;

                case 10:
                    switch (10) {
                        case 10:
                            value = 1;
                    }
            }
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 9)

