from besser.bot.core.entity.entity import Entity
from besser.bot.core.intent.intent_parameter import IntentParameter


class Intent:
    """The Intent core component of a bot.

    Intents define a set of training sentences representing the different ways a user could express an intention
    (e.g. "Hi", "Hello" for a Greetings intent).

    Intents can also define parameters that are filled with information extracted from the user input using entities.

    Args:
        name (str): the intent's name
        training_sentences (list[str] or None): the intent's training sentences
        parameters (list[IntentParameter] or None): the intent's parameters

    Attributes:
        name (str): The intent's name
        training_sentences (list[str]): The intent's training sentences
        processed_training_sentences (list[str]): Processed training sentences are stored for intent prediction
        parameters (list[IntentParameter]): The intent's parameters
    """

    def __init__(
            self,
            name: str,
            training_sentences: list[str] or None = None,
            parameters: list[IntentParameter] or None = None
    ):
        if parameters is None:
            parameters = []
        if training_sentences is None:
            training_sentences = []
        self.name: str = name
        self.training_sentences: list[str] = training_sentences
        self.processed_training_sentences: list[str] = []
        self.parameters: list[IntentParameter] = parameters

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def parameter(self, name: str, fragment: str, entity: Entity):
        """Add a parameter to the list of intent parameters.

        This method creates an :class:`IntentParameter` instance with the provided
        `name`, `fragment`, and `entity`, and appends it to the list of
        parameters associated with the intent.

        Args:
            name (str): The name of the parameter.
            fragment (str): A description or fragment associated with the parameter.
            entity (Entity): The entity that this parameter is related to.

        Returns:
            Intent: Returns the instance of :class:`Intent` it was called on (i.e., self).
        """
        # TODO: Check parameter not repeated
        self.parameters.append(IntentParameter(name, fragment, entity))
        return self
