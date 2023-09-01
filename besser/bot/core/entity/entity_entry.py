class EntityEntry:
    """
    Each one of the entries an entity consists of.

    :param value: the entry value
    :type value: str
    :param synonyms: the value synonyms
    :type value: list[str] or None

    :ivar str value: the entry value
    :ivar list[str] synonyms: the value synonyms
    :ivar str or None processed_value: processed value is stored for NER
    :ivar list[str] or None processed_synonyms: processed synonyms are stored for NER
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
