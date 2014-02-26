__author__ = 'samyvilar'

from collections import defaultdict
from itertools import chain
from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

from utils.symbol_table import SymbolTable

import front_end.parser as parser
import back_end.emitter.statements.statement as emitter

from back_end.loader.load import load
from back_end.emitter.stack_state import Stack
from back_end.emitter.cpu import evaluate, CPU, VirtualMemory
from back_end.linker.link import set_addresses
from back_end.virtual_machine.instructions.architecture import Halt

from test.test_back_end.test_emitter.test_declarations.test_definitions import TestDeclarations

from front_end.parser.ast.expressions import ConstantExpression, IntegerType
from back_end.emitter.expressions.expression import expression
from back_end.emitter.statements.statement import statement


class TestStatements(TestDeclarations):
    def evaluate(self, code):
        self.cpu, self.mem = CPU(), VirtualMemory()
        symbol_table = SymbolTable(
            (
                ('__ LABELS __', SymbolTable()),
                ('__ GOTOS __', defaultdict(list)),
                ('__ stack __', Stack()),
                ('__ expression __', expression),
                ('__ statement __', statement)
            )
        )

        load(
            set_addresses(
                chain(
                    emitter.statement(
                        next(parser.statement(
                            preprocess(tokenize(source(code))), SymbolTable((('__ LABELS __', SymbolTable()),)))
                        ),
                        symbol_table
                    ),
                    (Halt('__EOP__'),)
                )
            ),
            self.mem,
        )
        evaluate(self.cpu, self.mem)


class TestCompoundStatement(TestStatements):
    def test_compound_statement(self):
        source = """
        {
            int a = 10;
            {
                int a1 = 1;
            }
            a = a;
        }
        """
        super(TestCompoundStatement, self).evaluate(source)
        self.assert_base_element(ConstantExpression(10, IntegerType()))
