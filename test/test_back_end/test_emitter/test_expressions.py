__author__ = 'samyvilar'

from collections import defaultdict
from itertools import chain
from unittest import TestCase

from back_end.emitter.types import flatten

from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess

import front_end.parser.expressions.expression as parser
import back_end.emitter.expressions.expression as emitter
from back_end.emitter.cpu import evaluate, load, pop


class TestExpression(TestCase):
    def evaluate_expr(self, source):
        class CPU(object):
            def __init__(self):
                self.instr_pointer = 0
                self.zero, self.carry, self.overflow = 0, 0, 0
                self.stack_pointer, self.base_pointer = -1, -1
        self.mem, self.cpu = defaultdict(int), CPU()
        load(emitter.expression(parser.expression(Preprocess(Tokenize(source)))), self.mem, {})
        evaluate(self.cpu, self.mem)

    def test_binary_expr(self):
        source = '((int)(1) + (int)(2)) * (int)(3) - (float)(3.0)'
        self.evaluate_expr(source)
        self.assertEqual(pop(self.cpu, self.mem), eval(source))

    def test_unary_binary_expr(self):
        source = '~1 + (int)(2) * (int)(3) + (int)(4) & (int)(5) | (int)((int)(5) + ((float)(10.9) - (int)(2)))'
        self.evaluate_expr(source)
        self.assertEqual(pop(self.cpu, self.mem), eval(source))

    def test_binary_logical_expr(self):
        py_exp = '(int)(1) > (int)(3) and (int)(1) <= (int)(10) and (int)(25) ^ (not (int)(4)) ^ ((int)(5) and (int)(19) + (int)(10) - (not (float)(10.4)))'
        source = """
            #define or ||
            #define and &&
            #define not !

            """ + py_exp
        self.evaluate_expr(source)
        self.assertEqual(eval(py_exp), pop(self.cpu, self.mem))
