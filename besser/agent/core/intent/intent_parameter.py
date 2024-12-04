from besser.agent.core.entity.entity import Entity


class IntentParameter:
    """The intent parameter.

    An intent parameter is composed by a name, a fragment and an entity. The fragment is the intent's training sentence
    substring where an entity should be matched. E.g. in an intent with the training sentence
    "What is the weather in CITY?" we could define a parameter named "city" in the fragment "CITY" that should match
    with any value in the entity "city_entity" (previously defined)

    Args:
        name (str): the intent parameter name
        fragment (str): the fragment the intent's training sentences that is expected to match with the entity
        entity (Entity): the entity to be matched in this parameter

    Attributes:
        name (str): The intent parameter name
        fragment (str): The fragment the intent's training sentences that is expected to match with the entity
        entity (Entity): The entity to be matched in this parameter
    """

    def __init__(self, name: str, fragment: str, entity: Entity):
        self.name: str = name
        self.fragment: str = fragment
        self.entity: Entity = entity
