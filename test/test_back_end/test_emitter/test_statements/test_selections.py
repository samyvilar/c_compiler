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
        super(TestSelectionStatements, self).evaluate(source)
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
        super(TestSelectionStatements, self).evaluate(source)
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
        super(TestSelectionStatements, self).evaluate(source)
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
        super(TestSelectionStatements, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 12)

