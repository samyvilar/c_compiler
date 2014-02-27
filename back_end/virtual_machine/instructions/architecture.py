__author__ = 'samyvilar'

import sys
from inspect import isclass
from types import NoneType
from itertools import izip, chain, ifilter, imap, product, repeat, starmap, ifilterfalse, permutations

from front_end.loader.locations import LocationNotSet, loc
from utils import get_attribute_func

current_module = sys.modules[__name__]

ids = {}
operns = get_attribute_func('operands')
opern = lambda instr: operns(instr)[0]


class Instruction(object):  # No operand instruction.
    def __init__(self, location=LocationNotSet, instr_id=None):
        self.instruction_id = instr_id or ids[self.__class__]
        self.location = location

    def name(self):
        return self.__class__.__name__

    def __len__(self):
        return 1

    def __repr__(self):  # Simple instruction has no operands.
        return self.name()

    def __int__(self):
        return self.instruction_id

    def __iter__(self):
        yield self

    def __eq__(self, other):
        return type(other) is type(self)

    def __ne__(self, other):
        return not self.__eq__(other)


class Operand(object):
    def __init__(self, value, location=LocationNotSet):
        self.value = value
        self.location = location

    def __iter__(self):
        yield self

    def __int__(self):
        return int(self.value)

    def __long__(self):
        return long(self.value)

    def __str__(self):
        return self.__class__.__name__ + ' ' + str(self.value)

    def __float__(self):
        return float(self.value)


class Word(Operand):
    pass


class Integer(Word):
    pass


class Half(Operand):
    pass


class Quarter(Operand):
    pass


class OneEighth(Operand):
    pass


Byte = OneEighth


class Reference(Word):
    def __init__(self, obj, location=LocationNotSet):
        if type(obj) in {int, long}:  # If basic integer do nothing.
            super(Reference, self).__init__(obj, location)
        else:  # otherwise get the id of the object.
            super(Reference, self).__init__(id(obj), location)
        self.obj = obj

    def __str__(self):
        return self.__class__.__name__ + ' ' + str(self.obj)


referenced_obj = get_attribute_func('obj')


class Address(Reference):  # Address is a special operand since it can take other instructions or labels as operands
    pass


class Offset(Reference):  # similar to Address but mainly used for relative jumps ...
    pass


class RealOperand(Operand):
    pass


class Double(RealOperand):
    pass


class DoubleHalf(RealOperand):
    pass


class WideInstruction(Instruction):  # Instruction with a single operand
    def __init__(self, location, operand):
        self.operands = (operand,)
        super(WideInstruction, self).__init__(location)

    def __iter__(self):
        yield self
        for oper in self.operands:
            yield oper

    def __repr__(self):
        return '{oper_name} {operand}'.format(oper_name=self.name(), operand=self.operands[0])

    def __len__(self):
        return 2

    def __setitem__(self, key, value):
        assert key == 0
        self.operands = (value,)

    def __getitem__(self, item):
        return self.operands[item]

    def __eq__(self, other):
        return super(WideInstruction, self).__eq__(other) and self.operands == other.operands

    def __ne__(self, other):
        return not self.__eq__(other)


class Arithmetic(Instruction):
    pass


class Numeric(Arithmetic):
    pass


class Integral(Numeric):
    pass


class Halt(Instruction):
    pass


class Binary(Integral):
    pass


class Associative(Binary):
    pass


class Add(Associative):
    pass


class AddHalf(Associative):
    pass


class AddQuarter(Associative):
    pass


class AddOneEighth(Associative):
    pass


class Subtract(Binary):
    pass


class SubtractHalf(Binary):
    pass


class SubtractQuarter(Binary):
    pass


class SubtractOneEighth(Binary):
    pass


class Multiply(Associative):
    pass


class MultiplyHalf(Associative):
    pass


class MultiplyQuarter(Associative):
    pass


class MultiplyOneEighth(Associative):
    pass


class Divide(Binary):
    pass


class DivideHalf(Binary):
    pass


class DivideQuarter(Binary):
    pass


class DivideOneEighth(Binary):
    pass


class Compare(Binary):
    pass


class CompareHalf(Binary):
    pass


class CompareQuarter(Binary):
    pass


class CompareOneEighth(Binary):
    pass


class Mod(Binary):
    pass


class ModHalf(Binary):
    pass


class ModQuarter(Binary):
    pass


class ModOneEighth(Binary):
    pass


class BitWise(Integral):
    pass


class ShiftLeft(BitWise, Binary):
    pass


class ShiftLeftHalf(BitWise, Binary):
    pass


class ShiftLeftQuarter(BitWise, Binary):
    pass


class ShiftLeftOneEighth(BitWise, Binary):
    pass


class ShiftRight(BitWise, Binary):
    pass


class ShiftRightHalf(BitWise, Binary):
    pass


class ShiftRightQuarter(BitWise, Binary):
    pass


class ShiftRightOneEighth(BitWise, Binary):
    pass


class Or(BitWise, Associative):
    pass


class OrHalf(BitWise, Associative):
    pass


class OrQuarter(BitWise, Associative):
    pass


class OrOneEighth(BitWise, Associative):
    pass


class Xor(BitWise, Associative):
    pass


class XorHalf(BitWise, Associative):
    pass


class XorQuarter(BitWise, Associative):
    pass


class XorOneEighth(BitWise, Associative):
    pass


class And(BitWise, Associative):
    pass


class AndHalf(BitWise, Associative):
    pass


class AndQuarter(BitWise, Associative):
    pass


class AndOneEighth(BitWise, Associative):
    pass


class Unary(Numeric):
    pass


class Not(BitWise, Unary):
    pass


class NotHalf(BitWise, Unary):
    pass


class NotQuarter(BitWise, Unary):
    pass


class NotOneEighth(BitWise, Unary):
    pass


class NumericBinary(Numeric):
    pass


class AddFloat(NumericBinary):
    pass


class AddFloatHalf(NumericBinary):
    pass


class SubtractFloat(NumericBinary):
    pass


class SubtractFloatHalf(NumericBinary):
    pass


class MultiplyFloat(NumericBinary):
    pass


class MultiplyFloatHalf(NumericBinary):
    pass


class DivideFloat(NumericBinary):
    pass


class DivideFloatHalf(NumericBinary):
    pass


class CompareFloat(NumericBinary):
    pass


class CompareFloatHalf(NumericBinary):
    pass


class Jump(Instruction):
    pass


class AbsoluteJump(Jump):
    pass


class RelativeJump(WideInstruction, Jump):
    pass


class JumpFalse(RelativeJump):
    pass


class JumpFalseHalf(RelativeJump):
    pass


class JumpFalseQuarter(RelativeJump):
    pass


class JumpFalseOneEighth(RelativeJump):
    pass


class JumpTrue(RelativeJump):
    pass


class JumpTrueHalf(RelativeJump):
    pass


class JumpTrueQuarter(RelativeJump):
    pass


class JumpTrueOneEighth(RelativeJump):
    pass


class VariableLengthInstruction(WideInstruction):  # Instructions with more than one operand, mainly used for JumpTable
    def __len__(self):
        return 1 + len(self.operands)

    def __repr__(self):
        return '{oper_name} {operands}'.format(oper_name=self.name(), operand=self.operands)

    def __iter__(self):
        yield self
        for operand in self.operands:
            yield operand


class JumpTable(RelativeJump, VariableLengthInstruction):
    def __init__(self, location, cases):
        default_addr = cases.pop('default')  # pop default address to properly calculate number of cases ...
        operands = [default_addr, Word(len(cases), location)]
        _sorted_keys = sorted(cases.iterkeys())
        operands.extend(chain(_sorted_keys, (cases[key] for key in _sorted_keys)))

        super(JumpTable, self).__init__(location, operands)

        self.key_indices = {0: 'default'}
        self.key_indices.update(  # indices of operands ...
            (index, addr) for index, addr in enumerate(_sorted_keys, 2 + len(cases))
        )
        cases['default'] = default_addr  # add back default
        self.cases = cases
        self.operands = operands

    def __repr__(self):
        return super(JumpTable, self).name() + str(self.cases)

    def __setitem__(self, key, value):
        if key < 1 + len(self.cases):
            self.operands[key] = value
        else:
            self.cases[self.key_indices[key]] = value


class JumpTableHalf(JumpTable):
    pass


class JumpTableQuarter(JumpTable):
    pass


class JumpTableOneEighth(JumpTable):
    pass


class LoadRegister(Instruction):
    pass


class LoadPointer(LoadRegister):
    pass


class LoadBaseStackPointer(LoadPointer):
    # Pushes the current address of the base stack pointer, used to reference auto variables.
    pass


class SetBaseStackPointer(Instruction):
    pass


class LoadStackPointer(LoadPointer):
    pass


class SetStackPointer(Instruction):
    pass


class LoadInstructionPointer(LoadPointer):
    pass


class Allocate(WideInstruction):
    pass


class Dup(WideInstruction):
    pass


class Swap(WideInstruction):
    pass


class LoadFlagInstruction(LoadRegister):
    pass


class LoadZeroFlag(LoadFlagInstruction):  # numbers equal (sign or unsigned)
    pass


class LoadNonZeroFlag(LoadFlagInstruction):  # numbers don't equal  (sign or unsigned)
    pass


class LoadCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers less than
    pass


class LoadMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers less than
    pass


class LoadNonZeroNonCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers greater than
    pass


class LoadNonZeroNonMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers greater than
    pass


class LoadZeroCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers less than or equal
                                                     # (invert LoadNonZeroNonCarryBorrowFlag)
    pass


class LoadZeroMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers less than or equal
                                                  # invert LoadNonZeroNonMostSignificantBitFlag
                                                  # LoadZeroMostSignificantBitFlag
    pass


class LoadNonCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers greater than or equal
                                                    # invert LoadCarryBorrowFlag (LoadNonCarryBorrowFlag)
    pass


class LoadNonMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers greater than or equal
                                                     # invert LoadMostSignificantBitFlag (LoadNonMostSignificantBitFlag)
    pass


class Push(WideInstruction):
    pass


class PushHalf(WideInstruction):
    pass


class PushQuarter(WideInstruction):
    pass


class PushOneEighth(WideInstruction):
    pass


class Pop(Instruction):
    pass


class PopHalf(Instruction):
    pass


class PopQuarter(Instruction):
    pass


class PopOneEighth(Instruction):
    pass


class MoveInstruction(Instruction):
    pass


class WideMoveInstruction(MoveInstruction, WideInstruction):
    pass


class LoadInstruction(Instruction):
    pass


class Load(LoadInstruction, WideMoveInstruction):
    pass


class Set(WideMoveInstruction):
    pass


# Postfix increment and decrement instructions are extremely expensive on stack machines.
# As such lets create special instructions that implements them ...
class PostfixUpdate(WideInstruction):
    pass


class ConversionInstruction(Instruction):
    pass


class ConvertToFloatFrom(ConversionInstruction):
    pass


class ConvertToFloatFromHalf(ConversionInstruction):
    pass


class ConvertToFloatFromQuarter(ConversionInstruction):
    pass


class ConvertToFloatFromOneEighth(ConversionInstruction):
    pass


class ConvertToFloatFromSigned(ConversionInstruction):
    pass


class ConvertToFloatFromSignedHalf(ConversionInstruction):
    pass


class ConvertToFloatFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToFloatFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToFromFloat(ConversionInstruction):  # from float to Integer
    pass


class ConvertToFromHalf(ConversionInstruction):  # (half, quarter, one_eighth) => Integer
    pass


class ConvertToFromQuarter(ConversionInstruction):
    pass


class ConvertToFromOneEighth(ConversionInstruction):
    pass


class ConvertToHalfFrom(ConversionInstruction):  # Integer => (half, quarter, one_eighth)
    pass


class ConvertToQuarterFrom(ConversionInstruction):
    pass


class ConvertToOneEighthFrom(ConversionInstruction):
    pass


class ConvertToQuarterFromHalf(ConversionInstruction):  # half => (quarter, one_eighth)
    pass


class ConvertToOneEighthFromHalf(ConversionInstruction):
    pass


class ConvertToHalfFromQuarter(ConversionInstruction):  # quarter => (half, one_eighth)
    pass


class ConvertToOneEighthFromQuarter(ConversionInstruction):
    pass


class ConvertToQuarterFromOneEighth(ConversionInstruction):  # one_eighth => (quarter, half)
    pass


class ConvertToHalfFromOneEighth(ConversionInstruction):
    pass


class ConvertToFromHalfFloat(ConversionInstruction):
    pass


class ConvertToHalfFromFloat(ConversionInstruction):
    pass


class ConvertToHalfFromHalfFloat(ConversionInstruction):
    pass


class ConvertToQuarterFromFloat(ConversionInstruction):
    pass


class ConvertToQuarterFromHalfFloat(ConversionInstruction):
    pass


class ConvertToOneEighthFromFloat(ConversionInstruction):
    pass


class ConvertToOneEighthFromHalfFloat(ConversionInstruction):
    pass


class ConvertToSignedFromSignedHalf(ConversionInstruction):
    pass


class ConvertToSignedFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToSignedFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToSignedHalfFromSigned(ConversionInstruction):
    pass


class ConvertToSignedQuarterFromSigned(ConversionInstruction):
    pass


class ConvertToSignedOneEighthFromSigned(ConversionInstruction):
    pass


class ConvertToSignedQuarterFromSignedHalf(ConversionInstruction):
    pass


class ConvertToSignedOneEighthFromSignedHalf(ConversionInstruction):
    pass


class ConvertToSignedHalfFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToSignedOneEighthFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToSignedHalfFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToSignedQuarterFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToFromSignedHalf(ConversionInstruction):
    pass


class ConvertToFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToHalfFromSigned(ConversionInstruction):
    pass


class ConvertToQuarterFromSigned(ConversionInstruction):
    pass


class ConvertToOneEighthFromSigned(ConversionInstruction):
    pass


class ConvertToQuarterFromSignedHalf(ConversionInstruction):
    pass


class ConvertToOneEighthFromSignedHalf(ConversionInstruction):
    pass


class ConvertToHalfFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToOneEighthFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToHalfFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToQuarterFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToSignedFromHalf(ConversionInstruction):
    pass


class ConvertToSignedFromQuarter(ConversionInstruction):
    pass


class ConvertToSignedFromOneEighth(ConversionInstruction):
    pass


class ConvertToSignedHalfFrom(ConversionInstruction):
    pass


class ConvertToSignedQuarterFrom(ConversionInstruction):
    pass


class ConvertToSignedOneEighthFrom(ConversionInstruction):
    pass


class ConvertToSignedQuarterFromHalf(ConversionInstruction):
    pass


class ConvertToSignedOneEighthFromHalf(ConversionInstruction):
    pass


class ConvertToSignedHalfFromQuarter(ConversionInstruction):
    pass


class ConvertToSignedOneEighthFromQuarter(ConversionInstruction):
    pass


class ConvertToSignedHalfFromOneEighth(ConversionInstruction):
    pass


class ConvertToSignedQuarterFromOneEighth(ConversionInstruction):
    pass


class Pass(Instruction):  # Empty instruction similar to NOP
    pass


class SystemCall(Instruction):
    pass


class LoadSingle(LoadInstruction):
    pass


class LoadSingleHalf(LoadInstruction):
    pass


class LoadSingleQuarter(LoadInstruction):
    pass


class LoadSingleOneEighth(LoadInstruction):
    pass


class LoadHalf(LoadInstruction, WideInstruction):
    pass


class LoadQuarter(LoadInstruction, WideInstruction):
    pass


class LoadOneEighth(LoadInstruction, WideInstruction):
    pass


class PostfixUpdateHalf(WideInstruction):
    pass


class PostfixUpdateQuarter(WideInstruction):
    pass


class PostfixUpdateOneEighth(WideInstruction):
    pass


class DupSingle(Instruction):
    pass


class DupSingleHalf(Instruction):
    pass


class DupSingleQuarter(Instruction):
    pass


class DupSingleOneEighth(Instruction):
    pass


class DupHalf(WideInstruction):
    pass


class DupQuarter(WideInstruction):
    pass


class DupOneEighth(WideInstruction):
    pass


class SwapSingle(Instruction):
    pass


class SwapSingleHalf(Instruction):
    pass


class SwapSingleQuarter(Instruction):
    pass


class SwapSingleOneEighth(Instruction):
    pass


class SwapHalf(WideInstruction):
    pass


class SwapQuarter(WideInstruction):
    pass


class SwapOneEighth(WideInstruction):
    pass


class SetSingle(Instruction):
    pass


class SetSingleHalf(Instruction):
    pass


class SetSingleQuarter(Instruction):
    pass


class SetSingleOneEighth(Instruction):
    pass


class SetHalf(WideInstruction):
    pass


class SetQuarter(WideInstruction):
    pass


class SetOneEighth(WideInstruction):
    pass


class ConvertToFloatFromHalfFloat(ConversionInstruction):
    pass


class ConvertToHalfFloatFromFloat(ConversionInstruction):
    pass


class ConvertToHalfFloatFrom(ConversionInstruction):
    pass


class ConvertToHalfFloatFromSignedOneEighth(ConversionInstruction):
    pass


class ConvertToHalfFloatFromOneEighth(ConversionInstruction):
    pass


class ConvertToHalfFloatFromSignedHalf(ConversionInstruction):
    pass


class ConvertToHalfFloatFromHalf(ConversionInstruction):
    pass


class ConvertToHalfFloatFromSignedQuarter(ConversionInstruction):
    pass


class ConvertToHalfFloatFromSigned(ConversionInstruction):
    pass


class ConvertToHalfFloatFromQuarter(ConversionInstruction):
    pass


Loads = tuple(ifilter(lambda c: issubclass(c, LoadInstruction), ifilter(isclass, globals().itervalues())))

ids.update({
    Push:                                       2,
    Load:                                       3,
    PostfixUpdate:                              4,
    Dup:                                        5,
    Swap:                                       6,
    LoadBaseStackPointer:                       7,
    LoadStackPointer:                           8,
    Allocate:                                   9,
    Compare:                                    10,
    Add:                                        11,
    Multiply:                                   12,
    Mod:                                        13,
    ShiftLeft:                                  14,
    Or:                                         15,
    Xor:                                        16,
    Not:                                        17,
    AddFloat:                                   18,
    MultiplyFloat:                              19,
    AbsoluteJump:                               20,
    JumpFalse:                                  21,
    JumpTable:                                  22,
    ConvertToFloatFrom:                         23,
    ConvertToFloatFromSigned:                   24,
    RelativeJump:                               25,
    LoadZeroFlag:                               30,   # ==
    LoadCarryBorrowFlag:                        31,  # <, unsigned
    LoadMostSignificantBitFlag:                 32,  # < signed
    LoadNonZeroNonCarryBorrowFlag:              33,  # > unsigned
    LoadNonZeroNonMostSignificantBitFlag:       34,  # > signed

    AddHalf:                                    35,
    AddQuarter:                                 36,
    AddOneEighth:                               37,

    SubtractHalf:                               38,
    SubtractQuarter:                            39,
    SubtractOneEighth:                          40,

    MultiplyHalf:                               41,
    MultiplyQuarter:                            42,
    MultiplyOneEighth:                          43,

    DivideHalf:                                 44,
    DivideQuarter:                              45,
    DivideOneEighth:                            46,

    ModHalf:                                    47,
    ModQuarter:                                 48,
    ModOneEighth:                               49,

    ConvertToHalfFloatFromFloat:                50,

    OrHalf:                                     51,
    OrQuarter:                                  52,
    OrOneEighth:                                53,

    XorHalf:                                    54,
    XorQuarter:                                 55,
    XorOneEighth:                               56,

    AndHalf:                                    57,
    AndQuarter:                                 58,
    AndOneEighth:                               59,

    NotHalf:                                    60,
    NotQuarter:                                 61,
    NotOneEighth:                               62,

    PushHalf:                                   63,
    PushQuarter:                                64,
    PushOneEighth:                              65,

    PopHalf:                                    66,
    PopQuarter:                                 67,
    PopOneEighth:                               68,

    ConvertToFloatFromHalf:                     69,
    ConvertToFloatFromQuarter:                  70,
    ConvertToFloatFromOneEighth:                71,
    ConvertToFloatFromSignedHalf:               72,
    ConvertToFloatFromSignedQuarter:            73,
    ConvertToFloatFromSignedOneEighth:          74,

    ConvertToFromHalfFloat:                     75,
    ConvertToHalfFromFloat:                     76,
    ConvertToHalfFromHalfFloat:                 77,
    ConvertToQuarterFromFloat:                  78,
    ConvertToQuarterFromHalfFloat:              79,
    ConvertToOneEighthFromFloat:                80,
    ConvertToOneEighthFromHalfFloat:            81,

    CompareHalf:                                82,
    CompareQuarter:                             83,
    CompareOneEighth:                           84,
    CompareFloatHalf:                           85,

    ConvertToFromHalf:                          86,  # (half, quarter, one_eighth) => Integer
    ConvertToFromQuarter:                       87,
    ConvertToFromOneEighth:                     88,
    ConvertToHalfFrom:                          89,  # Integer => (half, quarter, one_eighth)
    ConvertToQuarterFrom:                       90,
    ConvertToOneEighthFrom:                     91,
    ConvertToQuarterFromHalf:                   92,  # half => (quarter, one_eighth)
    ConvertToOneEighthFromHalf:                 93,
    ConvertToHalfFromQuarter:                   94,  # quarter => (half, one_eighth)
    ConvertToOneEighthFromQuarter:              95,
    ConvertToHalfFromOneEighth:                 96,  # one_eighth => (half, quarter)
    ConvertToQuarterFromOneEighth:              97,

    ShiftLeftHalf:                              98,
    ShiftLeftQuarter:                           99,
    ShiftLeftOneEighth:                         100,
    ShiftRightHalf:                             101,
    ShiftRightQuarter:                          102,
    ShiftRightOneEighth:                        103,

    JumpTrueHalf:                               104,
    JumpTrueQuarter:                            105,
    JumpTrueOneEighth:                          106,
    JumpFalseHalf:                              107,
    JumpFalseQuarter:                           108,
    JumpFalseOneEighth:                         109,
    JumpTableHalf:                              110,
    JumpTableQuarter:                           111,
    JumpTableOneEighth:                         112,

    LoadSingle:                                 113,
    LoadSingleHalf:                             114,
    LoadSingleQuarter:                          115,
    LoadSingleOneEighth:                        116,

    LoadHalf:                                   117,
    LoadQuarter:                                118,
    LoadOneEighth:                              119,

    PostfixUpdateHalf:                          120,
    PostfixUpdateQuarter:                       121,
    PostfixUpdateOneEighth:                     122,

    ConvertToFloatFromHalfFloat:                123,

    DivideFloatHalf:                            124,
    MultiplyFloatHalf:                          125,
    SubtractFloatHalf:                          126,
    AddFloatHalf:                               127,

    DupSingle:                                  128,
    DupSingleHalf:                              129,
    DupSingleQuarter:                           130,
    DupSingleOneEighth:                         131,

    DupHalf:                                    132,
    DupQuarter:                                 133,
    DupOneEighth:                               134,

    SwapSingle:                                 135,
    SwapSingleHalf:                             136,
    SwapSingleQuarter:                          137,
    SwapSingleOneEighth:                        138,

    SwapHalf:                                   139,
    SwapQuarter:                                140,
    SwapOneEighth:                              141,

    SetSingle:                                  142,
    SetSingleHalf:                              143,
    SetSingleQuarter:                           144,
    SetSingleOneEighth:                         145,

    SetHalf:                                    146,
    SetQuarter:                                 147,
    SetOneEighth:                               148,

    ConvertToHalfFloatFrom:                     149,
    ConvertToHalfFloatFromSignedOneEighth:      150,
    ConvertToHalfFloatFromOneEighth:            151,
    ConvertToHalfFloatFromSignedHalf:           152,
    ConvertToHalfFloatFromHalf:                 153,
    ConvertToHalfFloatFromSignedQuarter:        154,
    ConvertToHalfFloatFromSigned:               155,
    ConvertToHalfFloatFromQuarter:              156,

    ConvertToSignedFromSignedHalf:              157,
    ConvertToSignedFromSignedQuarter:           158,
    ConvertToSignedFromSignedOneEighth:         159,
    ConvertToSignedHalfFromSigned:              160,
    ConvertToSignedQuarterFromSigned:           161,
    ConvertToSignedOneEighthFromSigned:         162,
    ConvertToSignedQuarterFromSignedHalf:       163,
    ConvertToSignedOneEighthFromSignedHalf:     164,
    ConvertToSignedHalfFromSignedQuarter:       165,
    ConvertToSignedOneEighthFromSignedQuarter:  166,
    ConvertToSignedHalfFromSignedOneEighth:     167,
    ConvertToSignedQuarterFromSignedOneEighth:  168,

    ConvertToFromSignedHalf:                    169,
    ConvertToFromSignedQuarter:                 170,
    ConvertToFromSignedOneEighth:               171,
    ConvertToHalfFromSigned:                    172,
    ConvertToQuarterFromSigned:                 173,
    ConvertToOneEighthFromSigned:               174,
    ConvertToQuarterFromSignedHalf:             175,
    ConvertToOneEighthFromSignedHalf:           176,
    ConvertToHalfFromSignedQuarter:             177,
    ConvertToOneEighthFromSignedQuarter:        178,
    ConvertToHalfFromSignedOneEighth:           179,
    ConvertToQuarterFromSignedOneEighth:        180,

    ConvertToSignedFromHalf:                    181,
    ConvertToSignedFromQuarter:                 182,
    ConvertToSignedFromOneEighth:               183,
    ConvertToSignedHalfFrom:                    184,
    ConvertToSignedQuarterFrom:                 185,
    ConvertToSignedOneEighthFrom:               186,
    ConvertToSignedQuarterFromHalf:             187,
    ConvertToSignedOneEighthFromHalf:           188,
    ConvertToSignedHalfFromQuarter:             189,
    ConvertToSignedOneEighthFromQuarter:        190,
    ConvertToSignedHalfFromOneEighth:           191,
    ConvertToSignedQuarterFromOneEighth:        192,


    Pass:                                       220,
    SystemCall:                                 221,
    LoadZeroMostSignificantBitFlag:             222,  # signed <=
    LoadZeroCarryBorrowFlag:                    223,  # unsigned <=
    LoadNonMostSignificantBitFlag:              224,  # signed >=
    LoadNonCarryBorrowFlag:                     225,  # unsigned >=
    LoadNonZeroFlag:                            226,   # !=

    ConvertToFromFloat:                         233,

    JumpTrue:                                   235,

    DivideFloat:                                237,
    SubtractFloat:                              238,
    And:                                        241,
    ShiftRight:                                 242,
    CompareFloat:                               243,
    Divide:                                     244,
    Subtract:                                   245,
    LoadInstructionPointer:                     246,
    SetStackPointer:                            248,
    SetBaseStackPointer:                        249,
    Set:                                        252,
    Pop:                                        254,
    Halt:                                       255,
})


def load_instruction_pointer(location):
    yield LoadInstructionPointer(location)


def load_non_zero_carry_borrow_flag(location):
    yield LoadNonZeroNonCarryBorrowFlag(location)


def load_non_zero_non_most_significant_bit_flag(location):
    yield LoadNonZeroNonMostSignificantBitFlag(location)

instr_objs = dict(izip(ids.itervalues(), ids.iterkeys()))
variable_length_instr_ids = dict(ifilter(lambda item: issubclass(item[0], VariableLengthInstruction), ids.iteritems()))
wide_instr_ids = dict(
    ifilter(
        lambda item: issubclass(item[0], WideInstruction) and not issubclass(item[0], VariableLengthInstruction),
        ids.iteritems()
    )
)
no_operand_instr_ids = dict(ifilterfalse(lambda item: issubclass(item[0], WideInstruction), ids.iteritems()))


def allocate(amount, location):
    if amount:
        yield Allocate(location, -amount)


def is_instr(gen, instr_name):
    # we use the __name__ for functions or check instance if its defined as a class ...
    return (getattr(gen, '__name__', '') == instr_name) or isinstance(gen, globals().get(instr_name, NoneType))


def is_load(gen):
    return is_instr(gen, 'load')


class single_iteration(object):
    def __iter__(self):
        # safe guard against multiple calls to __iter__ instruction are/(should be) emitted only once per instance
        if hasattr(self, 'emitted'):
            raise StopIteration
        # noinspection PyAttributeOutsideInit
        self.emitted = True
        # if ok call __iter__ on the next object not necessary a base class ...
        return super(single_iteration, self).__iter__()

    def next(self):
        raise TypeError

    def __next__(self):  # P3K uses __next__
        raise TypeError

    def __name__(self):
        return self.__class__.__name__(self)


class instruction(Instruction):  # represents an instruction iterator ...
    def __init__(self, location):
        self.instr_type = next(ifilter(lambda obj_type: obj_type in ids, self.__class__.mro()))
        super(instruction, self).__init__(location, instr_id=ids[self.instr_type])


def convert_to_camel_case_from_space(operation_name):
    return ''.join(
        (word[0].upper() + word[1:])
        for word in ifilter(None, imap(str.strip, operation_name.replace('_', ' ').split(' ')))
    )

_sizes = {8: '', 4: '_half', 2: '_quarter', 1: '_one_eighth'}  # convert integral operand size to instruction postfix
float_sizes = {8: '', 4: '_half'}  # convert real operand size to instruction name postfix ...


jump_table_by_max_value_instrs = {
    2**(operand_size * 8) - 1: getattr(current_module, convert_to_camel_case_from_space('jump_table' + postfix))
    for operand_size, postfix in _sizes.iteritems()
}


def jump_table(location, addresses, allocations, switch_max_value, switch_body_instrs):
    return chain(
        (jump_table_by_max_value_instrs[switch_max_value](location, addresses),),
        chain.from_iterable(allocations),
        switch_body_instrs
    )


def get_operations_by_size(instr_name, sizes=None):
    return {
        s: getattr(current_module, instr_name + postfix)
        for s, postfix in (sizes or _sizes).iteritems() if hasattr(current_module, instr_name + postfix)
    }


instructions_with_no_operand_alternative_instr_names = 'set', 'load', 'dup', 'swap'
for _name in instructions_with_no_operand_alternative_instr_names:
    setattr(
        current_module,
        _name + '_instrs',
        {s: convert_to_camel_case_from_space(_name + pf) for s, pf in _sizes.iteritems()}
    )


def get_single_alternative_if_present(instr_name, amount, location):
    if amount in getattr(current_module, instr_name + '_instrs'):
        instr = getattr(current_module, convert_to_camel_case_from_space(instr_name + '_single' + _sizes[amount]))(
            location
        )
    else:
        _operand_size = next(ifilterfalse(lambda i, amount=amount: amount % i, sorted(_sizes, reverse=True)), None)
        if not _operand_size:
            raise ValueError('{l} Could not find an appropriate instr type {n} for operand_amount {s}'.format(
                l=location, s=amount, n=instr_name
            ))
        instr = getattr(current_module, convert_to_camel_case_from_space(instr_name + _sizes[_operand_size]))(
            location, amount/_operand_size
        )
    return instr


def set_instr(stack_instrs, amount, location):
    return chain(stack_instrs, (get_single_alternative_if_present('set', amount, location),))


def load(instrs, amount, location):
    for value in instrs:  # return generator so we can check whether the instruction stream ends with a load type instr
        yield value
    yield get_single_alternative_if_present('load', amount, location)


def dup(amount, location):
    # expensive instruction requiring at a minimum 4 address translations (instr, operand, stack, stack - operand)
    if amount:
        yield get_single_alternative_if_present('dup', amount, location)


def dup_single(location):
    yield DupSingle(location)


def swap(amount, location):
    # very expensive instruction requiring at a minimum 4 address translations (instr, operand, stack, stack - operand)
    if amount:
        yield get_single_alternative_if_present('swap', amount, location)


def swap_single(location):
    yield SwapSingle(location)


def pop(location):
    yield Pop(location)


class push_constant(single_iteration):
    def __init__(self, value, location):
        assert isinstance(value, (int, long, float, Integer, Double))  # safe guard against bad API call ...
        self.value = value
        self.location = location

    def __iter__(self):
        yield Push(loc(self), self.value)


class push_integral(push_constant):
    core_type = long


class push_real(push_constant):
    core_type = float


def push_address(value, location):
    yield Push(location, value)


def push_half(value, location):
    yield PushHalf(location, value)


def push_quarter(value, location):
    yield PushQuarter(location, value)


def push_one_eighth(value, location):
    yield PushOneEighth(location, value)


def push(value, location):
    if isinstance(value, Address):
        return push_address(value, location)
    if isinstance(value, (int, long, Integer)):
        if isinstance(value, int):
            value = push_integral.core_type(value)  # TODO: fix this ...
        return push_integral(value, location)
    if isinstance(value, (float, Double)):
        return push_real(value, location)
    raise ValueError('{l} Expected Address/Integral/Real got {g}'.format(l=location, g=value))


def is_immediate_push(gen):
    return is_instr(gen, 'push_constant')


def get_immediate_pushed_value(instr):
    return instr.value


def postfix_update(addr, amount, location):
    return chain(addr, (PostfixUpdate(location, amount),))


def postfix_update_half(addr, amount, location):
    return chain(addr, (PostfixUpdateHalf(location, amount),))


def postfix_update_quarter(addr, amount, location):
    return chain(addr, (PostfixUpdateQuarter(location, amount),))


def postfix_update_one_eighth(addr, amount, location):
    return chain(addr, (PostfixUpdateOneEighth(location, amount),))


class arithmetic_operator(instruction):
    func = staticmethod(reduce)

    def __init__(self, *operands, **kwargs):
        self.operands = operands
        super(arithmetic_operator, self).__init__(kwargs.pop('location', LocationNotSet))

    def __iter__(self):
        if all(imap(is_immediate_push, self.operands)) and hasattr(self, 'operator'):
            opern = self.operands[0]
            assert len(set(imap(type, self.operands))) == 1  # safe guard against mixing types ...
            return iter(
                push(
                    self.func(   # apply python operator on operands converted to python types ...
                        getattr(opern.core_type, self.operator),  # get python operator
                        # get operands and convert them to python type
                        imap(opern.core_type, imap(get_immediate_pushed_value, self.operands))
                    ),
                    self.location
                )
            )

        return chain(chain.from_iterable(self.operands), (self.instr_type(self.location),))


class unary(arithmetic_operator, Unary):
    func = staticmethod(lambda oper, operands: oper(next(iter(operands))))

    def __init__(self, operand, location, operand_type=()):
        self.operand_type = operand_type
        super(unary, self).__init__(operand, location=location)


class binary(arithmetic_operator, Binary):
    def __init__(self, left_operand, right_operand, location, operand_types=()):
        self.operand_types = operand_types
        super(binary, self).__init__(left_operand, right_operand, location=location)

    @property
    def left_operand(self):
        return self.operands[0]

    @left_operand.setter
    def left_operand(self, value):
        self.operands = (value, self.right_operand)

    @property
    def right_operand(self):
        return self.operands[1]

    @right_operand.setter
    def right_operand(self, value):
        self.operands = (self.left_operand, value)


# class identity(binary):
#     def __init__(self, left_operand, right_operand, location, value):
#         self.identity_value = value
#         super(identity, self).__init__(left_operand, right_operand, location)
#
#
# class left_identity(identity):
#     def __iter__(self):
#         if is_immediate_push(self.left_operand) and \
#            get_immediate_pushed_value(self.left_operand) == self.identity_value:
#                 return iter(self.right_operand)
#
#         return super(left_identity, self).__iter__()
#
#
# class associative(binary):
#     def __iter__(self):  # first __iter__ in mro for associative operators ...
#         # Collapse associative operations +, *, |, & ... (1 + x) + 1 => (2 + x) ... (2 * x) * 4 => 8 * x ...
#
#         # check left operand ...
#         if isinstance(self.left_operand, getattr(self, 'instr_type', type)) and is_immediate_push(self.right_operand):
#             l, operand = loc(self.right_operand), get_immediate_pushed_value(self.right_operand)
#             if is_immediate_push(self.left_operand.left_operand):
#                 right_operand = get_immediate_pushed_value(self.left_operand.left_operand)
#                 self.left_operand.left_operand = \
#                     iter(self.__class__(push(operand, loc(self)), push(right_operand, l), l))  # collapse ...
#                 return iter(self.left_operand)
#
#             if is_immediate_push(self.left_operand.right_operand):
#                 l, right_operand = loc(self.left_operand.right_operand), \
#                     get_immediate_pushed_value(self.left_operand.right_operand)
#                 self.left_operand.right_operand = iter(self.__class__(push(operand, l), push(right_operand, l), l))
#                 return iter(self.left_operand)
#
#         # check right operand ...
#         if isinstance(self.right_operand, getattr(self, 'instr_type', type)) and is_immediate_push(self.left_operand):
#             l, operand = loc(self.left_operand), get_immediate_pushed_value(self.left_operand)
#             if is_immediate_push(self.right_operand.left_operand):
#                 right_operand, l = get_immediate_pushed_value(self.right_operand.left_operand),\
#                     loc(self.right_operand.left_operand)
#                 self.right_operand.left_operand = iter(self.__class__(push(operand, l), push(operand, l), l))
#                 return iter(self.right_operand)
#
#             if is_immediate_push(self.right_operand.right_operand):
#                 l, right_operand = loc(self.right_operand.right_operand), \
#                     get_immediate_pushed_value(self.right_operand.right_operand)
#                 self.right_operand.right_operand = iter(self.__class__(push(operand, l), push(operand, l), l))
#                 return iter(self.right_operand)
#
#         # no collapse continue ...
#         return super(associative, self).__iter__()
#
#
# class right_identity(identity):
#     def __iter__(self):  # first __iter__ for non-associative binary operators ...
#         if is_immediate_push(self.right_operand) and \
#            get_immediate_pushed_value(self.right_operand) == self.identity_value:
#                 return iter(self.left_operand)
#         return super(right_identity, self).__iter__()
#
#
# class __negative_one_identity__(identity):
#     def __init__(self, left_operand, right_operand, location):
#         super(__negative_one_identity__, self).__init__(left_operand, right_operand, location, -1)
#
#
# class __zero_identity__(identity):
#     def __init__(self, left_operand, right_operand, location):
#         super(__zero_identity__, self).__init__(left_operand, right_operand, location, 0)
#
#
# class __one_identity__(identity):
#     def __init__(self, left_operand, right_operand, location):
#         super(__one_identity__, self).__init__(left_operand, right_operand, location, 1)
#
#
# class left_zero_identity(__zero_identity__, left_identity):
#     pass
#
#
# class right_zero_identity(__zero_identity__, right_identity):
#     pass
#
#
# class left_one_identity(__one_identity__, left_identity):
#     pass
#
#
# class right_one_identity(__one_identity__, right_identity):
#     pass
#
#
# class negative_one_identity(__negative_one_identity__, left_identity, right_identity):
#     pass
#
#
# class zero_identity(left_zero_identity, right_zero_identity):
#     pass
#
#
# class one_identity(left_one_identity, right_one_identity):
#     pass
#
#
# class convert_to_right_shift(binary):
#     def __iter__(self):
#         if is_immediate_push(self.right_operand):
#             operand, l = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
#             if operand and not ((operand - 1) & operand):
#                 return iter(shift_right(self.left_operand, push(push_integral.core_type(log(operand, 2)), l), l))
#         return super(convert_to_right_shift, self).__iter__()
#
#
# class convert_to_left_shift(binary):  # converts constant multiplication to faster left shifts ...
#     def __iter__(self):
#         assert isinstance(self, Associative)  # safe-guard against non-associative instructions (-, /)
#         if is_immediate_push(self.right_operand):
#             operand, l = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
#             if operand and not ((operand - 1) & operand):  # is operand a non-zero power of 2
#                 return iter(shift_left(self.left_operand, push(push_integral.core_type(log(operand, 2)), l), l))
#
#         if is_immediate_push(self.left_operand):
#             operand, l = get_immediate_pushed_value(self.left_operand), loc(self.left_operand)
#             if operand and not((operand - 1) & operand):
#                 return iter(shift_left(self.right_operand, push(push_integral.core_type(log(operand, 2)), l), l))
#             self.left_operand = push(operand, l)
#
#         return super(convert_to_left_shift, self).__iter__()


def add_types_to_current_module(class_names, base_classes, attributes):
    for class_name, base_classes, attributes in izip(class_names, base_classes, attributes):
        setattr(current_module, class_name, type(class_name, base_classes, attributes))

integral_operation_postfixes = '', '_half', '_quarter', '_one_eighth'
real_operation_postfixes = '_float', '_float_half'
all_operation_postfixes = integral_operation_postfixes + real_operation_postfixes

_completely_implemented_operation_names = 'add', 'subtract', 'multiply', 'divide'


add_types_to_current_module(
    imap(''.join, product(_completely_implemented_operation_names, all_operation_postfixes)),
    izip(
        repeat(single_iteration),
        repeat(binary),
        imap(
            getattr,
            repeat(current_module),
            imap(
                convert_to_camel_case_from_space,
                imap(''.join, product(_completely_implemented_operation_names, all_operation_postfixes))
            )
        ),
    ),
    repeat({})
)


integral_implemented_operation_names = \
    'mod', 'shift_left', 'shift_right', 'bitwise_or',  'bitwise_xor', 'bitwise_and'

add_types_to_current_module(
    imap(''.join, product(integral_implemented_operation_names, integral_operation_postfixes)),
    izip(
        repeat(single_iteration),
        repeat(binary),
        imap(
            getattr,
            repeat(current_module),
            imap(
                convert_to_camel_case_from_space,
                (s.replace('bitwise_', '')
                 for s in imap(''.join, product(integral_implemented_operation_names, integral_operation_postfixes)))
            )
        )
    ),
    repeat({})
)

add_types_to_current_module(
    imap('not_bitwise'.__add__, integral_operation_postfixes),
    izip(
        repeat(single_iteration),
        repeat(unary),
        imap(
            getattr,
            repeat(current_module),
            imap(convert_to_camel_case_from_space, imap('not'.__add__, integral_operation_postfixes))
        )
    ),
    repeat({})
)


def compare(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (Compare(location),), chain.from_iterable(flags))


def compare_half(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (CompareHalf(location),), chain.from_iterable(flags))


def compare_quarter(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (CompareQuarter(location),), chain.from_iterable(flags))


def compare_one_eighth(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (CompareOneEighth(location),), chain.from_iterable(flags))


def compare_float(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (CompareFloat(location),), chain.from_iterable(flags))


def compare_float_half(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (CompareFloatHalf(location),), chain.from_iterable(flags))


float_conversion_postfixes = {8: '_float', 4: '_half_float'}
integral_conversion_postfixes = {8: '', 4: '_half', 2: '_quarter', 1: '_one_eighth'}
unsigned_conversion_postfixes = dict(izip(
    integral_conversion_postfixes.iterkeys(), imap('_unsigned'.__add__, integral_conversion_postfixes.itervalues())
))
signed_conversion_postfixes = dict(izip(
    integral_conversion_postfixes.iterkeys(), imap('_signed'.__add__, integral_conversion_postfixes.itervalues())
))

postfix_kinds = 'float', 'integral', 'unsigned', 'signed'
postfix_to_size = dict(imap(reversed, chain.from_iterable(
    getattr(current_module, pf_kind + '_conversion_postfixes').iteritems() for pf_kind in postfix_kinds
)))


def get_conversion_name(to_type, from_type):
    return 'convert_to' + to_type + '_from' + from_type


_filter_out_conversion_rules = set(
    starmap(
        get_conversion_name,
        chain(  # filter out same type conversions (word => word, float => float)
            imap(repeat, chain(
                float_conversion_postfixes.itervalues(),
                integral_conversion_postfixes.itervalues(),
                unsigned_conversion_postfixes.itervalues(),
                signed_conversion_postfixes.itervalues()
            ), repeat(2)),
            ifilter(    # filter out different sign type but same size type conversions (unsigned word to signed word)
                lambda pair: postfix_to_size[pair[0]] == postfix_to_size[pair[1]],
                permutations(chain(
                    integral_conversion_postfixes.itervalues(),
                    signed_conversion_postfixes.itervalues(),
                    unsigned_conversion_postfixes.itervalues()
                ), 2)
            ),
            # filter out conversion to sign from floats since converting from a float will always yield a signed int
            product(signed_conversion_postfixes.itervalues(), float_conversion_postfixes.itervalues()),
        )
    )
)

_conversion_to_float_types_class_names = tuple(
    ifilterfalse(
        _filter_out_conversion_rules.__contains__,
        starmap(get_conversion_name, product(
            float_conversion_postfixes.itervalues(),
            chain(
                float_conversion_postfixes.itervalues(),  # convert float => (unsigned/signed/float types)
                integral_conversion_postfixes.itervalues(),
                signed_conversion_postfixes.itervalues())))
    )
)

_conversion_to_integral_types_class_names = tuple(
    ifilterfalse(
        _filter_out_conversion_rules.__contains__,
        starmap(
            get_conversion_name,
            product(
                chain(integral_conversion_postfixes.itervalues(), signed_conversion_postfixes.itervalues()),
                chain(
                    float_conversion_postfixes.itervalues(),
                    integral_conversion_postfixes.itervalues(),
                    signed_conversion_postfixes.itervalues())))
    )
)

_all_conversion_names = tuple(chain(_conversion_to_float_types_class_names, _conversion_to_integral_types_class_names))

add_types_to_current_module(
    _all_conversion_names,
    izip(
        repeat(single_iteration),
        repeat(unary),
        imap(getattr, repeat(current_module), imap(convert_to_camel_case_from_space, _all_conversion_names))
    ),
    repeat({})
)


def load_stack_pointer(location):
    yield LoadStackPointer(location)


def set_stack_pointer(instrs, location):
    return chain(instrs, (SetStackPointer(location),))


def load_base_stack_pointer(location):
    yield LoadBaseStackPointer(location)


def set_base_stack_pointer(instrs, location):
    return chain(instrs, (SetBaseStackPointer(location),))


def load_zero_flag(location):
    yield LoadZeroFlag(location)


def load_non_zero_flag(location):
    yield LoadNonZeroFlag(location)


def load_carry_borrow_flag(location):
    yield LoadCarryBorrowFlag(location)


def load_most_significant_bit_flag(location):
    yield LoadMostSignificantBitFlag(location)


def load_zero_most_significant_bit_flag(location):
    yield LoadZeroMostSignificantBitFlag(location)


def load_zero_carry_borrow_flag(location):
    yield LoadZeroCarryBorrowFlag(location)


def load_non_carry_borrow_flag(location):
    yield LoadNonCarryBorrowFlag(location)


def load_non_most_significant_bit_flag(location):
    yield LoadNonMostSignificantBitFlag(location)


def halt(location):
    yield Halt(location)


def pass_instr(location):
    yield Pass(location)


def absolute_jump(instr, location):
    return chain(instr, (AbsoluteJump(location),))


for _name, _pf in product(('jump_false', 'jump_true'), _sizes.itervalues()):
    _func_name = _name + _pf
    _class_obj = getattr(current_module, convert_to_camel_case_from_space(_func_name))
    _func = lambda instrs, address, location, _class_obj=_class_obj: chain(instrs, (_class_obj(location, address),))
    _func.__name__ = _func_name
    setattr(current_module, _func_name, _func)


def relative_jump(address, location):
    yield RelativeJump(location, address)


from copy import deepcopy


def copy_operand(operand):
    if isinstance(operand, (int, long, float)):
        return operand
    if isinstance(operand, (Address, Offset)):
        return operand.__class__(operand.obj, loc(operand))
    if isinstance(operand, (Integer, Double)):
        return operand.__class__(operand.value, loc(operand))
    raise ValueError('Cannot copy operand: {g}'.format(g=operand))


def copy_instruction(instr):
    if isinstance(instr, JumpTable):
        return JumpTable(loc(instr), deepcopy(instr.cases))
    if isinstance(instr, VariableLengthInstruction):
        return instr.__class__(loc(instr), map(copy_operand, operns(instr)))
    if isinstance(instr, WideInstruction):
        return instr.__class__(loc(instr), copy_operand(opern(instr)))
    if isinstance(instr, Instruction):
        return instr.__class__(loc(instr))
    raise ValueError('Expected an instruction got {g}'.format(g=instr))


class logical(binary):
    def __init__(self, left_operand, right_operand, location, operand_types):
        self.default_instr, self.end_instr = Pass(location), Pass(location)
        super(logical, self).__init__(left_operand, right_operand, location, operand_types)


class logical_and(single_iteration, logical, And):  # it needs to reference an instruction in order to create the object
    def __iter__(self):
        # if is_immediate_push(self.left_operand) and is_immediate_push(self.right_operand):
        #     return iter(  # collapse constants
        #         push(
        #             push_integral.core_type(
        #                 all(imap(push_real.core_type, imap(get_immediate_pushed_value, self.operands)))
        #             ),
        #             self.location
        #         )
        #     )
        #
        # if is_immediate_push(self.left_operand):  # check left operand
        #     operand, location = get_immediate_pushed_value(self.left_operand), loc(self.left_operand)
        #     # if left operand is zero than simply push zero otherwise check right operand ...
        #     # use float just to be safe ...
        #     return iter(
        #         compare(self.right_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
        #         if push_real.core_type(operand)
        #         else push(0, loc(self))
        #     )
        #
        # if is_immediate_push(self.right_operand):  # check right operand
        #     # care must be taken if the right operand is constant zero since we still need to evaluate the left,
        #     # but we really don't need to apply expensive 'compare', simply pop the result ...
        #     operand, location = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
        #     return iter(
        #         compare(self.left_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
        #         if push_real.core_type(operand)
        #         else chain(self.left_operand, pop(self.location), push(0, self.location))
        #     )

        if isinstance(self.left_operand, logical_and):
            # check we are chaining && if so update the left operands false_instr instruction, so it can skip this one
            # or any other && expression.
            # we are parsing using right recursion, so the last operand will iterate first but emit last.
            self.left_operand.right_default_instr = getattr(self, 'right_default_instr', self.default_instr)

        return chain(
            get_jump_false(self.operand_types[1])(
                self.left_operand,
                Offset(getattr(self, 'right_default_instr', self.default_instr), self.location),
                self.location,
            ),
            get_compare(self.operand_types[2])(
                self.right_operand,
                get_push(self.operand_types[2])(0, self.location),
                self.location,
                (load_non_zero_flag(self.location),)
            ),
            relative_jump(Offset(self.end_instr, self.location), self.location),
            (self.default_instr,),
            get_push(self.operand_types[0])(0, self.location),
            (self.end_instr,),
        )


class logical_or(single_iteration, logical, Or):
    def __iter__(self):
        # if is_immediate_push(self.left_operand) and is_immediate_push(self.right_operand):
        #     return iter(
        #         push(
        #             push_integral.core_type(
        #                 any(imap(push_real.core_type, imap(get_immediate_pushed_value, self.operands)))
        #             ),
        #             self.location
        #         )
        #     )
        #
        # if is_immediate_push(self.left_operand):
        #     operand, location = get_immediate_pushed_value(self.left_operand), loc(self.left_operand)
        #     return iter(
        #         compare(self.right_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
        #         if push_real.core_type(operand)
        #         else push(1, location)
        #     )
        #
        # if is_immediate_push(self.right_operand):
        #     # again care must be taken if the right operand is 0, we still need to evaluate the left
        #     # but no need for COMPARE
        #     operand, location = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
        #     return iter(
        #         compare(self.left_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
        #         if push_real.core_type(operand)
        #         else chain(self.left_operand, pop(self.location), push(1, location))
        #     )

        if isinstance(self.left_operand, logical_or):
            self.left_operand.right_default_instr = getattr(self, 'right_default_instr', self.default_instr)

        return chain(
            get_jump_true(self.operand_types[1])(
                self.left_operand,
                Offset(getattr(self, 'right_default_instr', self.default_instr), self.location),
                self.location
            ),
            get_compare(self.operand_types[2])(
                self.right_operand,
                get_push(self.operand_types[2])(0, self.location),
                self.location,
                (load_non_zero_flag(self.location),)),
            relative_jump(Offset(self.end_instr, self.location), self.location),
            (self.default_instr,),
            get_push(self.operand_types[0])(1, self.location),
            (self.end_instr,),
        )


instr_word_names = 'pop', 'push', 'jump_false', 'jump_true', 'compare', 'not_bitwise', 'postfix_update'
for instr_name in instr_word_names:
    _size = get_operations_by_size(instr_name)
    setattr(current_module, instr_name + '_instrs', _size)
    setattr(current_module, 'get_' + instr_name, lambda operand_size, instrs=_size: instrs[operand_size])


compare_float_instrs = get_operations_by_size('compare_float', float_sizes)


def get_compare_float(operand_size):
    return compare_float_instrs[operand_size]


def set_single(stack_instrs, location, addr_instrs=()):
    return chain(stack_instrs, addr_instrs, (SetSingle(location),))


def set_single_half(stack_instrs, location, addr_instrs=()):
    return chain(stack_instrs, addr_instrs, (SetSingleHalf(location),))


def set_single_quarter(stack_instrs, location, addr_instrs=()):
    return chain(stack_instrs, addr_instrs, (SetSingleQuarter(location),))


def set_single_one_eighth(stack_instrs, location, addr_instrs=()):
    return chain(stack_instrs, addr_instrs, (SetSingleOneEighth(location),))


set_single_instrs = get_operations_by_size('set_single')


def get_set_single(operand_size):
    return set_single_instrs[operand_size]




