__author__ = 'samyvilar'

from collections import defaultdict, Iterable

from front_end import List
from front_end.loader.locations import loc
from front_end.parser.ast.general import Node, EmptyNode

from front_end.parser.ast.declarations import Declaration, Definition, Declarator, name

from front_end.parser.ast.expressions import ConstantExpression, SizeOfExpression, IdentifierExpression, TrueExpression
from front_end.parser.ast.expressions import EmptyExpression, exp
from front_end.parser.types import c_type, FunctionType, safe_type_coercion

from front_end.errors import error_if_not_type


class Statement(Node):
    pass


class EmptyStatement(Statement, EmptyNode):
    pass


class CompoundStatement(Statement, List):
    def __init__(self, statements, location):
        super(CompoundStatement, self).__init__(location)
        List.__init__(self, statements)


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
        if isinstance(statement, Declaration):
            raise ValueError('{l} statement {i} cannot have a declaration/definition as a body'.format(
                l=loc(statement), i=self
            ))
        self.statement = statement
        super(StatementBody, self).__init__(location)


class ExpressionBody(StatementBody):
    def __init__(self, exp, body, location):
        self.exp = exp
        super(ExpressionBody, self).__init__(body, location)


class IterationStatement(ExpressionBody):
    pass


class WhileStatement(IterationStatement):
    pass


class DoWhileStatement(IterationStatement):
    pass


class ForStatement(IterationStatement):
    def __init__(self, init_exp, loop_exp, upd_exp, stmnt, location):
        self.init_exp, self.upd_exp = init_exp, upd_exp
        super(ForStatement, self).__init__(loop_exp, stmnt, location)


class SelectionStatement(ExpressionBody):
    pass


class IfStatement(SelectionStatement):
    def __init__(self, exp, comp_statement, else_statement, location):
        self.else_statement = else_statement
        super(IfStatement, self).__init__(exp, comp_statement, location)


class ElseStatement(SelectionStatement):
    def __init__(self, stmnt, location):
        super(ElseStatement, self).__init__(TrueExpression(location), stmnt, location)


class SwitchStatement(SelectionStatement):
    def __init__(self, exp, comp_statement, location):
        self.cases = {}
        if not isinstance(comp_statement, CompoundStatement):
            raise ValueError('{l} switch expected a CompoundStatement as a body got {got}'.format(
                l=loc(comp_statement), got=comp_statement
            ))
        for stmnt in comp_statement:
            if not isinstance(stmnt, (Definition, CaseStatement)):
                raise ValueError('{l} switch stmnt start expects declaration/definition/case/default got {got}'.format(
                    l=loc(stmnt), got=stmnt
                ))
            if isinstance(stmnt, CaseStatement):
                break
        for stmnt in comp_statement:
            self._populate_cases(stmnt)
        super(SwitchStatement, self).__init__(exp, comp_statement, location)

    def _populate_cases(self, p_object):
        if isinstance(p_object, DefaultStatement):
            if '__default__' in self.cases:
                raise ValueError('{l} Duplicate default statement, previous at {at}'.format(
                    l=loc(p_object), at=loc(self.cases[exp(p_object)])
                ))
            self.cases['__default__'] = p_object
        elif isinstance(p_object, CaseStatement):
            if exp(exp(p_object)) in self.cases:
                raise ValueError('{l} Duplicate case statement, previous at {at}'.format(
                    l=loc(p_object), at=loc(self.cases[exp(p_object)])
                ))
            self.cases[exp(exp(p_object))] = p_object

    def append(self, p_object):
        self._populate_cases(p_object)
        super(SwitchStatement, self).statement.append(p_object)


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