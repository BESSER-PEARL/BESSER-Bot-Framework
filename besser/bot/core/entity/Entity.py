from besser.bot.core.entity.EntityEntry import EntityEntry


class Entity:

    def __init__(self, name: str, base_entity=False, entries=None):
        if entries is None:
            entries = {}
        self.name = name
        self.base_entity = base_entity
        if self.base_entity:
            self.entries = None
        else:
            self.entries: list[EntityEntry] = []
            for value, synonyms in entries.items():
                self.entries.append(EntityEntry(value, synonyms))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)
