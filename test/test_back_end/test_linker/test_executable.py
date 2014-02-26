__author__ = 'samyvilar'

from unittest import TestCase
from itertools import chain

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess
from front_end.parser.parse import parse

from utils.symbol_table import SymbolTable

from back_end.emitter.emit import emit
from back_end.linker.link import executable, set_addresses, resolve
from back_end.emitter.cpu import evaluate, CPU, VirtualMemory
from back_end.loader.load import load


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

        mem = VirtualMemory()
        cpu = CPU()
        symbol_table = SymbolTable()
        load(
            set_addresses(
                resolve(
                    executable(
                        chain.from_iterable(emit(parse(preprocess(tokenize(source(code))))) for code in source_codes),
                        symbol_table
                    ),
                    symbol_table
                ),
            ),
            mem
        )
        evaluate(cpu, mem)