__author__ = 'samyvilar'

from itertools import imap


def encode(instr, word_type):
    return imap(word_type, instr)


def addresses(initial_address, step_size):
    while True:
        yield initial_address
        initial_address += step_size
