__author__ = 'samyvilar'

from unittest import TestCase
from front_end.tokenizer.tokenize import Tokenize
from front_end.parser.expressions.expression import expression


class TestExpressions(TestCase):
    def test_binary_expressions(self):
        expressions = (
            ('1 + 2 - 3 * 7 / 4', -2),
            ('1 >> 2 + 3 << 2 + 5', 0),
            ('1 || 0 + 4 - 10.5 / 1 && 0', 1),
            ('(1 + 2) * (1.0 + 2.0 + 3)', 18.0)
        )

        for raw_exp, expected_result in expressions:
            actual_result = expression(Tokenize(raw_exp), {})
            self.assertEqual(
                expected_result, actual_result.exp,
                'Raw exp {exp}, expected {e}, got {g}'.format(exp=raw_exp, e=expected_result, g=actual_result.exp)
            )

