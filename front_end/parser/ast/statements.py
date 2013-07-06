__author__ = 'samyvilar'

from collections import defaultdict, Iterable

from sequences import peek
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.ast.general import Node, EmptyNode

from front_end.parser.ast.declarations import Declaration, Definition, Declarator, name, initialization

from front_end.parser.ast.expressions import ConstantExpression, SizeOfExpression, IdentifierExpression, TrueExpression
from front_end.parser.ast.expressions import EmptyExpression, exp
from front_end.parser.types import c_type, FunctionType, safe_type_coercion

from front_end.errors import error_if_not_type


class FunctionDefinition(Definition):
    def __init__(self, c_decl, body):
        _ = error_if_not_type([c_type(c_decl)], FunctionType)
        if not all(isinstance(arg, Declarator) for arg in c_type(c_decl)):
            raise ValueError('{l} FunctionDef must have concrete declarators as params'.format(l=loc(c_type(c_decl))))
        if not isinstance(body, CompoundStatement):
            raise ValueError('{l} FunctionDef body is not a compound statement, got {g}'.format(l=loc(c_decl), g=body))
        super(FunctionDefinition, self).__init__(name(c_decl), c_type(c_decl), body, loc(c_decl), c_decl.storage_class)


class Statement(Node):
    pass


class EmptyStatement(Statement, EmptyNode):
    pass


class CompoundStatement(Statement):
    def __init__(self, statements, location):
        self.statements = statements
        super(CompoundStatement, self).__init__(location)

    def __iter__(self):
        return self.statements


class JumpStatement(Statement):
    pass


class GotoStatement(JumpStatement):
    def __init__(self, label, location):
        self.label = label
        super(GotoStatement, self).__init__(location)


class ContinueStatement(JumpStatement):
    pass


class BreakStatement(JumpStatement):
    pass


class ReturnStatement(JumpStatement):
    def __init__(self, exp, location):
        self.exp = exp
        super(ReturnStatement, self).__init__(location)


class StatementBody(Statement):
    def __init__(self, statement, location):
        self._statement = statement
        super(StatementBody, self).__init__(location)

    @property
    def statement(self):
        stmnt = next(self._statement)
        if isinstance(stmnt, Declaration):
            raise ValueError('{l} statement {i} cannot have a declaration/definition as a body'.format(
                l=loc(stmnt), i=self
            ))
        return stmnt


class ExpressionBody(StatementBody):
    def __init__(self, exp, body, location):
        self.exp = exp
        super(ExpressionBody, self).__init__(body, location)


class IterationStatement(ExpressionBody):
    pass


class WhileStatement(IterationStatement):
    pass


class DoWhileStatement(IterationStatement):
    @property
    def exp(self):
        return next(self._exp)

    @exp.setter
    def exp(self, value):
        self._exp = value


class ForStatement(IterationStatement):
    def __init__(self, init_exp, loop_exp, upd_exp, stmnt, location):
        self.init_exp, self.upd_exp = init_exp, upd_exp
        super(ForStatement, self).__init__(loop_exp, stmnt, location)


class SelectionStatement(ExpressionBody):
    pass


class IfStatement(SelectionStatement):
    def __init__(self, exp, comp_statement, location):
        super(IfStatement, self).__init__(exp, comp_statement, location)


class ElseStatement(SelectionStatement):
    def __init__(self, stmnt, location):
        super(ElseStatement, self).__init__(TrueExpression(location), stmnt, location)


class SwitchStatement(SelectionStatement):
    def __init__(self, exp, comp_statement, location):
        self.exp = exp
        super(SwitchStatement, self).__init__(exp, comp_statement, location)

    def __iter__(self):  # TODO: check...
        compound_stmnt = next(iter(super(SwitchStatement, self)))
        self.cases = {}
        for stmnt in compound_stmnt:
            if not isinstance(stmnt, (Definition, CaseStatement)):
                raise ValueError('{l} switch stmnt start expects declaration/definition/case/default got {got}'.format(
                    l=loc(stmnt), got=stmnt
                ))
            if isinstance(stmnt, DefaultStatement):
                if '__default__' in self.cases:
                    raise ValueError('{l} Duplicate default statement, previous at {at}'.format(
                        l=loc(stmnt), at=loc(self.cases[exp(stmnt)])
                    ))
                self.cases['__default__'] = stmnt
            elif isinstance(stmnt, CaseStatement):
                if exp(exp(stmnt)) in self.cases:
                    raise ValueError('{l} Duplicate case statement, previous at {at}'.format(
                        l=loc(stmnt), at=loc(self.cases[exp(stmnt)])
                    ))
            yield stmnt


class LabelStatement(StatementBody):
    def __init__(self, name, statement, location):
        self._name = name
        super(LabelStatement, self).__init__(statement, location)

    @property
    def name(self):
        return LabelStatement.get_name(self._name)

    @staticmethod
    def get_name(value):
        return value and 'label {n}'.format(n=value)


class CaseStatement(SelectionStatement):
    pass


class DefaultStatement(CaseStatement):
    def __init__(self, statement, location):
        super(DefaultStatement, self).__init__(TrueExpression(location), statement, location)


def no_effect(stmnt):
    return no_effect.rules[type(stmnt)]
no_effect.rules = defaultdict(lambda: False)
no_effect.rules.update({
    EmptyStatement: lambda stmnt: True,
    EmptyExpression: lambda stmnt: True,
    ConstantExpression: lambda stmnt: True,
    SizeOfExpression: lambda stmnt: True,
    IdentifierExpression:  lambda stmnt: True,
})