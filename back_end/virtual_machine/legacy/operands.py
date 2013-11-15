__author__ = 'samyvilar'


def oprn(cpu, mem):
    return mem[cpu.instr_pointer + cpu.word_type(1)]


def oprns(cpu, mem, count):
    one = cpu.word_type(1)
    addr = cpu.instr_pointer + one
    while count:
        yield mem[cpu.instr_pointer + addr]
        count -= one
        addr += one
