__author__ = 'samyvilar'

from StringIO import StringIO
from itertools import product, starmap, ifilter
from os import path

from c_comp import instrs, std_include_dirs, std_libraries_dirs, std_libraries

from back_end.emitter.cpu import evaluate, CPU, VirtualMemory, Kernel
from back_end.linker.link import set_addresses
from back_end.loader.load import load

from back_end.emitter.system_calls import CALLS
from test.test_back_end.test_emitter.test_declarations.test_definitions import TestDeclarations


class TestStdLib(TestDeclarations):
    def evaluate(self, code, cpu=None, mem=None, os=None):
        self.cpu, self.mem, self.os = cpu or CPU(), mem or VirtualMemory(), os or Kernel(CALLS)
        load(set_addresses(
            instrs(
                (StringIO(code),),
                std_include_dirs,
                libraries=ifilter(path.isfile, starmap(path.join, product(std_libraries_dirs, std_libraries)))
            )
        ), self.mem)
        evaluate(self.cpu, self.mem, self.os)