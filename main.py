__author__ = 'samyvilar'

from front_end.loader.load import Load
from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess
from front_end.parser.parse import Parse

from back_end.emitter.emit import Emit
from back_end.linker.link import Link



c_file = Link(
    Emit(
        Parse(
            Preprocess(
                Tokenize(
                    Load('test.c')
                )
            )
        )
    )
)