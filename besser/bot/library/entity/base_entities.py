from enum import Enum

from besser.bot.core.entity.entity import Entity

_PREFIX = '@sys.'


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

number_entity = Entity(BaseEntities.NUMBER.value, base_entity=True)
"""The `number` base entity."""

datetime_entity = Entity(BaseEntities.DATETIME.value, base_entity=True)
"""The `date-time` base entity."""

any_entity = Entity(BaseEntities.ANY.value, base_entity=True)
"""The `any` base entity."""
