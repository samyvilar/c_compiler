#! /usr/bin/python
__author__ = 'samyvilar'

import argparse
from collections import defaultdict

try:
    import cPickle as pickle
except ImportError as _:
    import pickle

from back_end.emitter.cpu import load, CPU, Kernel, evaluate
from back_end.emitter.system_calls import CALLS


def start(instrs):
    mem = defaultdict(int)
    cpu = CPU()
    kernel = Kernel(CALLS)
    load(instrs, mem)
    evaluate(cpu, mem, kernel)


def main():
    cli = argparse.ArgumentParser(description='Object Based Virtual Machine')
    cli.add_argument('binary_file', nargs=1, help='Executable file (pickled list of Instruction of objects...)')

    args = cli.parse_args(('a.out.p',))

    with open(args.binary_file[0]) as input_file:
        instrs = pickle.load(input_file)

    start(instrs)


if __name__ == '__main__':
    main()
