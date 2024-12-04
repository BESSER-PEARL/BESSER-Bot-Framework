from enum import Enum

from besser.agent.core.entity.entity import Entity

_PREFIX = 'base.'


class BaseEntities(Enum):
    """Enumeration of supported base entity types. This enumeration defines their names."""

    NUMBER = _PREFIX + 'number'
    """The `number` base entity."""

    DATETIME = _PREFIX + 'date-time'
    """The `date-time` base entity."""

    ANY = _PREFIX + 'any'
    """The `any` base entity."""


ordered_base_entities = [
    BaseEntities.DATETIME,
    BaseEntities.NUMBER,
    BaseEntities.ANY
]
"""This list specifies the order in which base entities must be searched in a user message. For instance, in
an intent with a number and a date-time parameter, the number is searched after date-times have been searched since a
date-time can contain numbers and matching first a number would interfere in the date-time entity."""

number_entity = Entity(
    name=BaseEntities.NUMBER.value,
    base_entity=True,
    description='An entity that matches any number'
)
"""The `number` base entity."""

datetime_entity = Entity(
    name=BaseEntities.DATETIME.value,
    base_entity=True,
    description='An entity that matches any date, time or datetime value'
)
"""The `date-time` base entity."""

any_entity = Entity(
    name=BaseEntities.ANY.value,
    base_entity=True,
    description='An entity that matches any text'
)
"""The `any` base entity."""
