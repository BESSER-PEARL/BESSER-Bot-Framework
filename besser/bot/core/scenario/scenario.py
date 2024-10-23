from enum import Enum
from typing import Union

from besser.bot.core.scenario.scenario_element import ScenarioElement
from besser.bot.core.session import Session


class ExpressionOperator(Enum):
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'


class Expression:

    def __init__(self, operator: ExpressionOperator, expressions: list[Union['Expression', ScenarioElement]]):
        # TODO: Run SAT solver to evaluate satisfiability of expression
        # Some libraries: pip install z3-solver, python-sat, pyminisat, pycosat
        # TODO: Convert to CNF? (OR conjunctions only)

        if operator in [ExpressionOperator.AND, ExpressionOperator.OR] and len(expressions) < 2:
            raise ValueError(f'Operator {operator} requires at least 2 expressions')
        if operator == ExpressionOperator.NOT and len(expressions) != 1:
            raise ValueError(f'Operator {operator} requires 1 expression')
        self.operator: ExpressionOperator = operator
        self.expressions: list[Union[Expression, ScenarioElement]] = expressions

    def __str__(self):
        return f'{self.operator}{[expression.__str__() for expression in self.expressions]}'

    def evaluate(self, session: Session) -> bool:
        if self.operator == ExpressionOperator.AND:
            return all([expression.evaluate(session) for expression in self.expressions])
        if self.operator == ExpressionOperator.OR:
            return any([expression.evaluate(session) for expression in self.expressions])
        if self.operator == ExpressionOperator.NOT:
            return not self.expressions[0].evaluate(session)


class Scenario:

    def __init__(self, name: str):
        self.name: str = name
        self.expression: Expression = None

    def __str__(self):
        return self.expression.__str__()

    def set_expression(self, expression: Expression) -> None:
        self.expression = expression

    def evaluate(self, session: Session) -> bool:
        return self.expression.evaluate(session)


def and_ex(expressions: list[Union[Expression, ScenarioElement]]) -> Expression:
    return Expression(operator=ExpressionOperator.AND, expressions=expressions)


def or_ex(expressions: list[Union[Expression, ScenarioElement]]) -> Expression:
    return Expression(operator=ExpressionOperator.OR, expressions=expressions)


def not_ex(expression: Union[Expression, ScenarioElement]) -> Expression:
    return Expression(operator=ExpressionOperator.NOT, expressions=[expression])
