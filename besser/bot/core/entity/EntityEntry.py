class EntityEntry:
    """Each one of the entries (and its synonyms) a CustomEntity consists of"""

    def __init__(self, value: str, synonyms=None):
        if synonyms is None:
            synonyms = []
        self.value: str = value
        self.synonyms: list[str] = synonyms
        self.preprocessed_value: str or None = None
        self.preprocessed_synonyms: list[str] or None = None
