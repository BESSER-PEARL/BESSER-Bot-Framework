from typing import TYPE_CHECKING

from besser.agent.core.entity.entity_entry import EntityEntry
from besser.agent.nlp.preprocessing.text_preprocessing import process_text

if TYPE_CHECKING:
    from besser.agent.nlp.nlp_engine import NLPEngine


class Entity:
    """The Entity core component of an agent.

    Entities are used to specify the type of information to extract from user inputs. These entities are embedded in
    intent parameters.

    Args:
        name (str): the entity's name
        base_entity (bool): whether the entity is base or not (i.e. custom)
        entries (dict[str, list[str]] or None): the entity entries. If base_entity, there are no entries (i.e. None)
        description (str or None): a description of the entity, optional

    Attributes:
        name (str): The entity's name
        base_entity (bool): Whether the entity is base or not (i.e. custom)
        entries (list[EntityEntry] or None): The entity entries. If base_entity, there are no entries (i.e. None)
        description (str or None): a description of the entity, optional
    """

    def __init__(
            self,
            name: str,
            base_entity: bool = False,
            entries: dict[str, list[str]] or None = None,
            description: str or None = None
    ):
        if entries is None:
            entries = {}
        self.name: str = name
        self.description = description
        self.base_entity: bool = base_entity
        self.entries: list[EntityEntry] or None = None
        if not self.base_entity:
            self.entries = []
            for value, synonyms in entries.items():
                self.entries.append(EntityEntry(value, synonyms))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def process_entity_entries(self, nlp_engine: 'NLPEngine') -> None:
        """Process the entity entries.

        Args:
            nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
        """
        if not self.base_entity:
            for entry in self.entries:
                entry.processed_value = process_text(entry.value, nlp_engine)
                entry.processed_synonyms = []
                for synonym in entry.synonyms:
                    entry.processed_synonyms.append(process_text(synonym, nlp_engine))

    def to_json(self) -> dict:
        """Returns the entity content in a JSON format.

        Returns:
            dict: The entity content.
        """
        entity_json = {
            'base_entity': self.base_entity,
            'description': self.description,
            'entries': []
        }
        if not self.base_entity:
            for entry in self.entries:
                entry_dict = {
                    'value': entry.value,
                    'synonyms': entry.synonyms
                }
                entity_json['entries'].append(entry_dict)
        return entity_json
