__author__ = 'samyvilar'

from itertools import imap, izip
from back_end.emitter.types import flatten


def encode(instr, word_type):
    return imap(word_type, flatten(instr))


def addresses(initial_address, step_size):
    while True:
        yield initial_address
        initial_address += step_size
