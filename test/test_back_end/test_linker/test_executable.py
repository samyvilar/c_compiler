__author__ = 'samyvilar'

from unittest import TestCase
from back_end.loader.load import load
from back_end.linker.link import executable
from back_end.emitter.emit import Emit

from front_end.parser.declarations.declarations import translation_unit
from front_end.preprocessor.preprocess import Preprocess
from front_end.tokenizer.tokenize import Tokenize


class TestExecutable(TestCase):
    def test_executable(self):
        source_files = """
            extern int b;
            int main()
            {
                b = 10;
                return 0;
            }
        """, "int b;"

        machine = load(
            executable(
                Emit(
                    translation_unit(
                        Preprocess(
                            Tokenize(
                                source
                            )
                        )
                    )
                ) for source in source_files
            )
        )
        machine.start()