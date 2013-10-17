#! /usr/bin/python
__author__ = 'samyvilar'

from optparse import OptionParser

import os
import inspect
try:
    import cPickle as pickle
except ImportError as e:
    import pickle

from itertools import chain, izip, starmap, repeat

from sequences import peek, takewhile

from front_end.loader.locations import loc, Location, EOFLocation
import front_end.loader.load as loader
import front_end.tokenizer.tokenize as tokenizer
import front_end.preprocessor.preprocess as preprocessor
import front_end.parser.parse as parser
from front_end.parser.symbol_table import SymbolTable
import back_end.emitter.emit as emitter
import back_end.linker.link as linker

import back_end.emitter.system_calls as system_calls

import ovm


def get_line(tokens):
    return takewhile(
        lambda t, line_number=loc(peek(tokens, EOFLocation)).line_number: loc(t).line_number == line_number, tokens
    )


def get_lines(tokens):
    while True:
        yield loc(peek(tokens)).line_number, get_line(tokens)


def format_line_tokens(tokens):
    temp = ''
    try:
        prev_token = next(tokens)
        temp += ' ' * (loc(prev_token).column_number - 1) + repr(prev_token)
    except StopIteration as _:
        return ''
    for token in tokens:
        if loc(prev_token).column_number + len(repr(prev_token)) != loc(token).column_number:
            temp += ' '
        temp += repr(token)
        prev_token = token
    return temp


def preprocess(files, include_dirs):
    output = ''
    for input_file in files:
        tokens = preprocessor.preprocess(tokenizer.tokenize(loader.load(input_file)), include_dirs=include_dirs)
        prev_line_number = loc(peek(tokens, Location('', 1, 1))).line_number - 1
        for line_number, line in get_lines(tokens):
            if line_number != prev_line_number + 1:
                output += os.linesep
            output += format_line_tokens(line) + os.linesep
            prev_line_number = line_number
    return output


def symbols(file_name, include_dirs=()):
    if isinstance(file_name, str) and os.path.splitext(file_name)[1] == '.o.p':
        with open(file_name) as file_obj:
            symbol_table = pickle.load(file_obj)
        symbol_seq = symbol_table.itervalues()
    else:
        symbol_seq = emitter.emit(
            parser.parse(
                preprocessor.preprocess(tokenizer.tokenize(loader.load(file_name)), include_dirs=include_dirs)
            )
        )
    return symbol_seq


curr_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
str_src_dirs = [os.path.join(curr_dir, 'stdlib', 'src')]
std_include_dirs = [curr_dir, os.path.join(curr_dir, 'stdlib', 'include')]
std_libraries_dirs = [curr_dir, os.path.join(curr_dir, 'stdlib', 'libs')]
std_libraries = ['libc.p']
std_symbols = system_calls.SYMBOLS


def instrs(files, include_dirs=(), library_dirs=(), libraries=()):
    symbol_table = SymbolTable()
    return linker.resolve(
        linker.executable(
            chain(std_symbols.itervalues(), chain.from_iterable(starmap(symbols, izip(files, repeat(include_dirs))))),
            symbol_table=symbol_table,
            libraries=libraries,
            library_dirs=library_dirs,
            linker=linker.static,
        ),
        symbol_table
    )


def main():
    cli = OptionParser()

    cli.add_option('-E', '--preprocess', action='store_true', default=False, help='Output preprocessor and stop.')
    cli.add_option('-c', '--compile', action='store_true', default=False, help='Compile, but not link.')
    cli.add_option('--static', '--static', action='store_true', default=True, help='Static Linking (default).')
    cli.add_option('--shared', '--shared', action='store_true', default=False, help='Shared Linking.')
    cli.add_option('--ovm', action='store_true', default=False, help='Execute code on the Object Based Virtual Mach.')
    cli.add_option('-a', '--archive', action='store_true', default=False, help='Archive files into a single output')

    cli.add_option('-o', '--output', default=[], nargs='?', action='append',
                   help='Name of output, file(s) default is the original')

    cli.add_option('-I', '--Include', default=[], nargs='?', action='append',
                   help='Directories to be used by the preprocessor')

    cli.add_option('-L', '--Libraries', default=[], nargs='?', action='append',
                   help='Directories to be used to search for libraries')

    cli.add_option('-l', '--libraries', default=[], nargs='?', action='append',
                   help='Name of libraries to search for symbols')

    options, files = cli.parse_args()

    options.Include += std_include_dirs
    options.Libraries += std_libraries_dirs
    options.libraries += std_libraries

    if options.preprocess:
        print(preprocess(files, options.Include))
    elif options.compile:
        if options.output:
            if len(options.output) != len(files):
                raise ValueError('Expected {e} but got {g} output file names.'.format(
                    e=len(files), g=len(options.output)
                ))
            output_files = options.output
        else:
            output_files = (os.path.splitext(file_name)[0] + '.o.p' for file_name in files)

        for input_file, output_file in izip(files, output_files):
            symbol_table = linker.library(symbols(input_file, options.Include))
            with open(output_file, 'wb') as file_obj:
                pickle.dump(symbol_table, file_obj)
    elif options.archive:
        symbol_table = SymbolTable()
        for input_file in files:
            symbol_table = linker.library(symbols(input_file, options.Include), symbol_table)
        if len(options.output) != 1:
            raise ValueError('Need exactly one output archive name got {g}'.format(g=len(options.output)))
        with open(options.output[0], 'wb') as file_obj:
            pickle.dump(symbol_table, file_obj)
    elif options.shared:
        raise NotImplementedError
    else:  # static linking ...
        instructions = instrs(files, options.Include, options.Libraries, options.libraries)

        if len(options.output) > 1:
            raise ValueError('Cannot specify more than 1 output for binary got {g}'.format(
                g=len(options.output)
            ))
        if options.ovm:
            ovm.start(instructions)
        else:
            instructions = tuple(instructions)

            file_output = options.output and options.output[0] or 'a.out.p'
            with open(file_output, 'wb') as file_obj:
                pickle.dump(instructions, file_obj)


if __name__ == '__main__':
    main()