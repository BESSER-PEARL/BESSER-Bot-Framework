class EntityEntry:
    """Each one of the entries an entity consists of.

    Args:
        value (str): the entry value
        synonyms (list[str] or None): the value synonyms

    Attributes:
        value (str): the entry value
        synonyms (list[str]): The value synonyms
        processed_value (str or None): Processed value is stored for NER
        processed_synonyms (list[str] or None): Processed synonyms are stored for NER
    """

    def __init__(
            self,
            value: str,
            synonyms: list[str] or None = None
    ):
        if synonyms is None:
            synonyms = []
        self.value: str = value
        self.synonyms: list[str] = synonyms
        self.processed_value: str or None = None
        self.processed_synonyms: list[str] or None = None
