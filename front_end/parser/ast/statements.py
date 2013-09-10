__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc, LocationNotSet
from front_end.parser.ast.general import Node, EmptyNode

from front_end.parser.ast.declarations import Declaration, Definition, Declarator, name

from front_end.parser.ast.expressions import ConstantExpression, SizeOfExpression, IdentifierExpression, TrueExpression
from front_end.parser.ast.expressions import EmptyExpression, Expression
from front_end.parser.types import c_type, FunctionType

from front_end.errors import error_if_not_type


class FunctionDefinition(Definition):
    def __init__(self, c_decl, body):
        _ = error_if_not_type(c_type(c_decl), FunctionType)
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
        if not isinstance(stmnt, (Expression, Statement)):
            raise ValueError('{l} statement {i} expected either expression/statement as a body got {g}'.format(
                l=loc(stmnt), i=self, g=stmnt
            ))
        return stmnt


class ExpressionBody(StatementBody):
    def __init__(self, exp, body, location):
        self.exp = exp
        super(ExpressionBody, self).__init__(body, location)


class IterationStatement(ExpressionBody):
    pass


class ForStatement(IterationStatement):
    def __init__(self, init_exp, loop_exp, upd_exp, stmnt, location):
        self.init_exp, self.upd_exp = init_exp, upd_exp
        super(ForStatement, self).__init__(loop_exp, stmnt, location)


class WhileStatement(IterationStatement):
    pass


class DoWhileStatement(IterationStatement):
    @property  # do while statement is the only iteration statement that calculates the expr after the body ...
    def exp(self):
        return next(self._exp)

    @exp.setter
    def exp(self, value):
        self._exp = value


class SelectionStatement(ExpressionBody):
    pass


class IfStatement(SelectionStatement):
    def __init__(self, exp, comp_statement, else_statement, location):
        self._else_statement = else_statement
        super(IfStatement, self).__init__(exp, comp_statement, location)

    @property
    def else_statement(self):
        return next(self._else_statement)


class ElseStatement(SelectionStatement):
    def __init__(self, stmnt, location):
        super(ElseStatement, self).__init__(TrueExpression(location), stmnt, location)


class SwitchStatement(SelectionStatement):
    @property
    def statement(self):
        stmnt = super(SwitchStatement, self).statement
        if not isinstance(stmnt, CompoundStatement):
            raise ValueError('{l} switch statement expected compound statement, got {g}'.format(l=loc(stmnt), g=stmnt))

        def _check_for_declarations(comp_statement):
            for gener in comp_statement:
                yield gener
            _ = super(SwitchStatement, self).statement  # Pop symbol table after completion...

        stmnt.statements = _check_for_declarations(stmnt.statements)
        return stmnt


class LabelStatement(StatementBody):
    def __init__(self, name, statement, location):
        self.name = name
        super(LabelStatement, self).__init__(statement, location)


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