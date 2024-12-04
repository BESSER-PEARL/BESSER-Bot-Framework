class MatchedParameter:
    """A matched parameter by the NER (i.e. an entity that is found in a user message, which is an intent parameter).

    Args:
        name (str): the parameter name
        value (object or None): the parameter value
        info (dict or None): extra parameter information

    Attributes:
        name (str): The parameter name
        value (object or None): The parameter value
        info (dict): Extra parameter information
    """

    def __init__(self,
                 name: str,
                 value: object or None = None,
                 info: dict or None = None):

        if info is None:
            info = {}
        self.name: str = name
        self.value: object or None = value
        self.info: dict = info
