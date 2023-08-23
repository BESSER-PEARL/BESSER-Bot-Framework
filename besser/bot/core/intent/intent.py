from besser.bot.core.intent.intent_parameter import IntentParameter


class Intent:

    def __init__(self, name: str, training_sentences=None, parameters=None):
        if parameters is None:
            parameters = []
        if training_sentences is None:
            training_sentences = []
        self.name: str = name
        self.training_sentences: list[str] = training_sentences
        self.processed_training_sentences = []
        self.parameters: list[IntentParameter] = parameters

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def parameter(self, name, fragment, entity):
        # TODO: Check parameter not repeated
        self.parameters.append(IntentParameter(name, fragment, entity))
        return self
