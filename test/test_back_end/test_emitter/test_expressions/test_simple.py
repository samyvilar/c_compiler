__author__ = 'samyvilar'

from collections import defaultdict
from unittest import TestCase

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

import front_end.parser.expressions.expression as parser
import back_end.emitter.expressions.expression as emitter
from back_end.emitter.cpu import evaluate, load, pop, CPU


class TestRawExpression(TestCase):
    def evaluate_expr(self, code):
        self.mem, self.cpu = defaultdict(int), CPU()
        load(emitter.expression(parser.expression(preprocess(tokenize(source(code))))), self.mem, {})
        evaluate(self.cpu, self.mem)

    def test_binary_expr(self):
        source = '((int)(1) + (int)(2)) * (int)(3) - (int)((float)(3.0)) / (int)(1) >> (int)(2) * (int)(1) << (int)(2)'
        self.evaluate_expr(source)
        self.assertEqual(pop(self.cpu, self.mem), eval(source))

    def test_unary_binary_expr(self):
        source = '~1 + (int)(2) * (int)(3) + (int)(4) & (int)(5) | (int)((int)(5) + ((float)(10.9) - (int)(2)))'
        self.evaluate_expr(source)
        self.assertEqual(pop(self.cpu, self.mem), eval(source))

    def test_binary_logical_expr(self):
        py_exp = '(int)(1) > (int)(3) and (int)(1) <= (int)(10) and' + \
                 '(int)(25) != (not (int)(4)) ^ ((int)(5) == (int)(19) + (int)(10) - (not (float)(10.4)))'
        source = """
            #define or ||
            #define and &&
            #define not !

            """ + py_exp
        self.evaluate_expr(source)
        self.assertEqual(eval(py_exp), pop(self.cpu, self.mem))
