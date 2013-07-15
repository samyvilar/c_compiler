__author__ = 'samyvilar'

from unittest import TestCase
from itertools import chain
from collections import defaultdict

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess
from front_end.parser.parse import parse

from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.emit import emit
from back_end.linker.link import executable
from back_end.emitter.cpu import load, evaluate, CPU


class TestExecutable(TestCase):
    def test_executable(self):
        source_codes = """
            extern int b;
            int main()
            {
                b = 10;
                return 0;
            }
        """, 'int b;'

        mem = defaultdict(int)
        cpu = CPU()
        symbol_table = SymbolTable()
        load(
            executable(
                chain.from_iterable(emit(parse(preprocess(tokenize(source(code))))) for code in source_codes),
                symbol_table
            ),
            mem,
            symbol_table,
        )

        evaluate(cpu, mem)