class MatchedParameter:

    def __init__(self, name: str, value=None, info=None):
        if info is None:
            info = {}
        self.name = name
        self.value = value
        self.info = info
