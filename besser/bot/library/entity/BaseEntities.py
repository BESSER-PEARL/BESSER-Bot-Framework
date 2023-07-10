PREFIX = '@sys.'


class BaseEntities:
    """ The enumeration of supported base entity types """

    NUMBER = PREFIX + 'number'
    DATETIME = PREFIX + 'date-time'
    ANY = PREFIX + 'any'


ordered_base_entities = [
    BaseEntities.DATETIME,
    BaseEntities.NUMBER,
    BaseEntities.ANY
]
