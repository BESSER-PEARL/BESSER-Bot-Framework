from besser.bot.core.entity.Entity import Entity


class IntentParameter:

    def __init__(self, name: str, fragment: str, entity: Entity):
        self.name: str = name
        self.fragment: str = fragment
        self.entity: Entity = entity
