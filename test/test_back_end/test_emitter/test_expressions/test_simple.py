__author__ = 'samyvilar'

from itertools import chain
from unittest import TestCase

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

import front_end.parser as parser

from front_end.parser.types import integer_type

from back_end.emitter.emit import expression as emit_expression
from back_end.emitter.c_types import get_word_type_name

from back_end.emitter.cpu import evaluate, CPU, VirtualMemory, base_element, word_type_factories
from back_end.loader.load import load
from back_end.linker.link import set_addresses

from back_end.virtual_machine.instructions.architecture import Halt


class TestRawExpression(TestCase):
    def evaluate_expr(self, code):
        self.mem, self.cpu = VirtualMemory(), CPU()
        load(
            set_addresses(
                chain(emit_expression(parser.expression(preprocess(tokenize(source(code))))), (Halt('__EOP__'),)),
            ),
            self.mem
        )
        evaluate(self.cpu, self.mem)

    def test_binary_expr(self):
        source = '((int)(1) + (int)(2)) * (int)(3) - (int)((float)(3.0)) / (int)(1) >> (int)(2) * (int)(1) << (int)(2)'
        self.evaluate_expr(source)
        self.assertEqual(
            base_element(self.cpu, self.mem, word_type_factories[get_word_type_name(integer_type)]),
            eval(source)
        )

    def test_unary_binary_expr(self):
        source = '~1 + (int)(2) * (int)(3) + (int)(4) & (int)(5) | (int)((int)(5) + ((float)(10.9) - (int)(2)))'
        self.evaluate_expr(source)
        self.assertEqual(
            base_element(self.cpu, self.mem, word_type_factories[get_word_type_name(integer_type)]),
            eval(source)
        )

    def test_binary_logical_expr(self):
        py_exp = '(int)((int)(1) > (int)(3) and (int)(1) <= (int)(10) and' + \
                 '(int)(25) != (not (int)(4)) ^ ((int)(5) == (int)(19) + (int)(10) - (not (float)(10.4))))'
        code = """
            #define or ||
            #define and &&
            #define not !

            """ + py_exp
        self.evaluate_expr(code)
        self.assertEqual(
            base_element(self.cpu, self.mem, word_type_factories[get_word_type_name(integer_type)]),
            eval(py_exp)
        )