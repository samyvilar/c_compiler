#! /usr/bin/env python
__author__ = 'samyvilar'

import argparse

try:
    import cPickle as pickle
except ImportError as _:
    import pickle

from back_end.emitter.cpu import CPU, VirtualMemory, Kernel, evaluate
from back_end.linker.link import set_addresses
from back_end.emitter.system_calls import CALLS
from back_end.loader.load import load


def start(instrs):
    mem = VirtualMemory()
    cpu = CPU()
    os = Kernel(CALLS)
    load(set_addresses(instrs), mem)
    evaluate(cpu, mem, os)


def main():
    cli = argparse.ArgumentParser(description='Virtual Machine')
    cli.add_argument('binary_file', nargs=1, help='Executable file (pickled list of Instruction of objects...)')

    args = cli.parse_args()

    with open(args.binary_file[0]) as input_file:
        instrs = pickle.load(input_file)

    start(instrs)


if __name__ == '__main__':
    main()
