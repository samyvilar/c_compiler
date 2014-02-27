#! /usr/bin/env python
__author__ = 'samyvilar'

import argparse
import os
import sys
import inspect

from itertools import imap, ifilter, product

from collections import OrderedDict

try:
    import cPickle as pickle
except ImportError as e:
    import pickle

from itertools import chain, izip, starmap, repeat

from utils.sequences import peek, takewhile, peek_or_terminal, terminal, consume_all, exhaust

from front_end.loader.locations import loc, line_number, column_number, Location
from front_end.tokenizer.tokens import IGNORE
import front_end.loader.load as loader
import front_end.tokenizer.tokenize as tokenizer
import front_end.preprocessor.preprocess as preprocessor
import front_end.parser.parse as parser
from utils.symbol_table import SymbolTable
import back_end.emitter.emit as emitter
import back_end.linker.link as linker
from back_end.loader.load import load as load_binaries

import back_end.emitter.system_calls as system_calls

from back_end.virtual_machine.instructions.architecture import Instruction

from back_end.emitter.optimizer.optimize import optimize, zero_level_optimization, first_level_optimization

from utils.errors import error_if_not_value
from utils.rules import identity

import vm

curr_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(curr_dir)


def get_line(tokens):
    return iter(()) if peek_or_terminal(tokens) is terminal else takewhile(
        lambda t, current_line_number=line_number(peek(tokens)): line_number(t) == current_line_number,
        tokens
    )


def format_line(line):
    prev_token = IGNORE(location=Location('', 0, 0))
    for token in consume_all(line):
        yield ' ' * (column_number(token) - (column_number(prev_token) + len(prev_token)))
        yield repr(token)
        prev_token = token
    yield os.linesep


def format_token_seq(token_seq):
    return chain.from_iterable(imap(format_line, imap(get_line, takewhile(peek, repeat(token_seq)))))


def preprocess_file(input_file, include_dirs):
    return preprocessor.preprocess(tokenizer.tokenize(loader.load(input_file)), include_dirs=include_dirs)


def preprocess(files, include_dirs):
    return chain.from_iterable(imap(format_token_seq, imap(preprocess_file, files, repeat(include_dirs))))


def symbols(file_name, include_dirs=(), optimizer=identity):
    if isinstance(file_name, str) and file_name.endswith('.o.p'):
        with open(file_name) as file_obj:
            symbol_table = pickle.load(file_obj)
        symbol_seq = symbol_table.itervalues()
    else:
        symbol_seq = optimizer(
            emitter.emit(
                parser.parse(
                    preprocessor.preprocess(tokenizer.tokenize(loader.load(file_name)), include_dirs=include_dirs)
                )
            )
        )
    return symbol_seq


str_src_dirs = [os.path.join(curr_dir, 'stdlib', 'src')]
std_include_dirs = [curr_dir, os.path.join(curr_dir, 'stdlib', 'include')]
std_libraries_dirs = [curr_dir, os.path.join(curr_dir, 'stdlib', 'libs')]
std_libraries = ['libc.p']
std_symbols = system_calls.SYMBOLS


def instrs(files, include_dirs=(), libraries=(), optimizer=identity):
    symbol_table = SymbolTable()
    return optimizer(
        linker.resolve(
            linker.executable(
                chain(
                    std_symbols.itervalues(), chain.from_iterable(starmap(symbols, izip(files, repeat(include_dirs))))
                ),
                symbol_table=symbol_table,
                libraries=libraries,
                linker=linker.static,
            ),
            symbol_table
        )
    )


def assembly(files, includes=(), libraries=(), optimizer=identity):
    mem = OrderedDict()
    load_binaries(linker.set_addresses(instrs(files, includes, libraries, optimizer)), mem)
    for addr, instr in ifilter(lambda i: isinstance(i[1], Instruction), mem.iteritems()):
        yield '{l}:{addr}: {elem}\n'.format(l=loc(instr), addr=addr, elem=instr)


def main():
    cli = argparse.ArgumentParser(description='C Compiler ...')

    cli.add_argument('files', nargs='+')
    cli.add_argument('-O', '--optimize', default=0, nargs=1, help='Optimization Level')
    cli.add_argument('-E', '--preprocess', action='store_true', default=False, help='Output preprocessor and stop.')
    cli.add_argument('-S', '--assembly', action='store_true', default=False, help='Output instructions readable text.')
    cli.add_argument('-c', '--compile', action='store_true', default=False, help='Compile, but not link.')
    cli.add_argument('-static', '--static', action='store_true', default=True, help='Static Linking (default).')
    cli.add_argument('-shared', '--shared', action='store_true', default=False, help='Shared Linking.')
    cli.add_argument('--vm', action='store_true', default=False, help='Execute code on Virtual Machine.')
    cli.add_argument('-a', '--archive', action='store_true', default=False, help='Archive files into a single output')

    cli.add_argument('-o', '--output', default=[], nargs='?', action='append',
                     help='Name of output, file(s) default is the original')

    cli.add_argument('-I', '--Include', default=[], nargs='?', action='append',
                     help='Directories to be used by the preprocessor when searching for files.')

    cli.add_argument('-L', '--Libraries', default=[], nargs='?', action='append',
                     help='Directories to be used by the linker when searching for libraries')

    cli.add_argument('-l', '--libraries', default=[], nargs='?', action='append',
                     help='Name of libraries to be used when searching for symbols.')

    args = cli.parse_args()
    args.Include += std_include_dirs + list(set(imap(os.path.dirname, args.files)))
    args.Libraries += std_libraries_dirs
    args.libraries += std_libraries

    libraries = ifilter(os.path.isfile, starmap(os.path.join, product(args.Libraries, args.libraries)))

    optimizer = lambda instrs: optimize(instrs, zero_level_optimization)
    if args.optimize and args.optimize[0] == '1':
        optimizer = lambda instrs: optimize(instrs, first_level_optimization)

    if args.preprocess:
        exhaust(imap(sys.stdout.write, preprocess(args.files, args.Include)))
    elif args.assembly:
        exhaust(imap(sys.stdout.write, assembly(args.files, args.Include, libraries, optimizer)))
    elif args.compile:
        if args.output:  # if output(s) giving then check it matches the number of inputs ...
            output_files = error_if_not_value(repeat(len(args.output), 1), len(args.files)) and args.output
        else:
            output_files = imap('{0}.o.p'.format, imap(lambda f: os.path.splitext(f)[0], args.files))

        for input_file, output_file in izip(args.files, output_files):
            symbol_table = linker.library(symbols(input_file, args.Include, optimizer))
            with open(output_file, 'wb') as file_obj:
                pickle.dump(symbol_table, file_obj)
    elif args.archive:
        symbol_table = SymbolTable()
        error_if_not_value(repeat(len(args.output), 1), 1)  # archives require a single output which has no default ...
        for input_file in args.files:  # compile all files into a single symbol_table ...
            symbol_table = linker.library(symbols(input_file, args.Include, optimizer), symbol_table)
        with open(args.output[0], 'wb') as file_obj:  # dump symbol_table ...
            pickle.dump(symbol_table, file_obj)
    elif args.shared:
        raise NotImplementedError
    else:  # default compile, and and statically link ...
        instructions = instrs(args.files, args.Include, libraries, optimizer)

        if args.vm:  # if we requested a vm then execute instructions ...
            vm.start(instructions)
        else:  # other wise emit single executable file ...
            _ = args.output and error_if_not_value(repeat(len(args.output), 1), 1, Location('cc.py', '', ''))
            file_output = args.output and args.output[0] or 'a.out.p'  # if not giving an output use default a.out.p
            with open(file_output, 'wb') as file_obj:
                pickle.dump(tuple(instructions), file_obj)


if __name__ == '__main__':
    main()