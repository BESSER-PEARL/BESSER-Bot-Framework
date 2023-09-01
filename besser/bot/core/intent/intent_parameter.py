from besser.bot.core.entity.entity import Entity


class IntentParameter:
    """
    The intent parameter.

    An intent parameter is composed by a name, a fragment and an entity. The fragment is the intent's training sentence
    substring where an entity should be matched. E.g. in an intent with the training sentence
    "What is the weather in CITY?" we could define a parameter named "city" in the fragment "CITY" that should match
    with any value in the entity "city_entity" (previously defined)

    :param name: the intent parameter name
    :type name: str
    :param fragment: the fragment the intent's training sentences that is expected to match with the entity
    :type fragment: str
    :param entity: the entity to be matched in this parameter
    :type entity: Entity


    :ivar str name: the intent parameter name
    :ivar str fragment: the fragment the intent's training sentences that is expected to match with the entity
    :ivar Entity entity: the entity to be matched in this parameter
    """

    def __init__(self, name: str, fragment: str, entity: Entity):
        self.name: str = name
        self.fragment: str = fragment
        self.entity: Entity = entity
