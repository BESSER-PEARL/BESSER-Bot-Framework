from abc import ABC


class IntentClassifierConfiguration(ABC):
    """The Intent Classifier Configuration abstract class.

    This configuration is assigned to a state, allowing the customization of its intent classifier.

    This class serves as a template to implement intent classifier configurations for the different Intent Classifiers.
    """

    def __init__(self):
        pass


class SimpleIntentClassifierConfiguration(IntentClassifierConfiguration):
    """The Simple Intent Classifier Configuration class.

    It allows the customization of a
    :class:`~besser.agent.nlp.intent_classifier.simple_intent_classifier.SimpleIntentClassifier`.

    Args:
        num_words (int): Max num of words to keep in the index of words
        num_epochs (int): Number of epochs to be run during training
        embedding_dim (int): Number of embedding dimensions to be used when embedding the words
        input_max_num_tokens (int): Max length for the vector representing a sentence
        discard_oov_sentences (bool): whether to automatically assign zero probabilities to sentences with all tokens
            being oov ones or not
        check_exact_prediction_match (bool): Whether to check for exact match between the sentence to predict and one of
            the training sentences or not
        activation_last_layer (str): The activation function of the last layer
        activation_hidden_layers (str): The activation function of the hidden layers
        lr (float): Learning rate for the optimizer

    Attributes:
        num_words (int): Max num of words to keep in the index of words
        num_epochs (int): Number of epochs to be run during training
        embedding_dim (int): Number of embedding dimensions to be used when embedding the words
        input_max_num_tokens (int): Max length for the vector representing a sentence
        discard_oov_sentences (bool): whether to automatically assign zero probabilities to sentences with all tokens
            being oov ones or not
        check_exact_prediction_match (bool): Whether to check for exact match between the sentence to predict and one of
            the training sentences or not
        activation_last_layer (str): The activation function of the last layer
        activation_hidden_layers (str): The activation function of the hidden layers
        lr (float): Learning rate for the optimizer
    """

    def __init__(
            self,
            num_words: int = 1000,
            num_epochs: int = 300,
            embedding_dim: int = 128,
            input_max_num_tokens: int = 15,
            discard_oov_sentences: bool = True,
            check_exact_prediction_match: bool = True,
            activation_last_layer: str = 'sigmoid',
            activation_hidden_layers: str = 'tanh',
            lr: float = 0.001,
    ):
        super().__init__()
        self.num_words: int = num_words
        self.num_epochs: int = num_epochs
        self.embedding_dim: int = embedding_dim
        self.input_max_num_tokens: int = input_max_num_tokens
        self.discard_oov_sentences: bool = discard_oov_sentences
        self.check_exact_prediction_match: bool = check_exact_prediction_match
        self.activation_last_layer: str = activation_last_layer
        self.activation_hidden_layers: str = activation_hidden_layers
        self.lr: float = lr


class LLMIntentClassifierConfiguration(IntentClassifierConfiguration):
    """The LLM Intent Classifier Configuration class.

    It allows the customization of a
    :class:`~besser.agent.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier`.

    Args:
        llm_name (str): the name of the LLM to be used (must be created in the agent)
        parameters (dict): the LLM parameters (this will vary depending on the suite and the LLM)
        use_intent_descriptions (bool): whether to include the intent descriptions in the LLM prompt
        use_training_sentences (bool): whether to include the intent training sentences in the LLM prompt
        use_entity_descriptions (bool): whether to include the entity descriptions in the LLM prompt
        use_entity_synonyms (bool): whether to include the entity value's synonyms in the LLM prompt

    Attributes:
        llm_name (str): the name of the LLM to be used (must be created in  the agent)
        parameters (dict): the LLM parameters (this will vary depending on the suite and the LLM)
        use_intent_descriptions (bool): whether to include the intent descriptions in the LLM prompt
        use_training_sentences (bool): whether to include the intent training sentences in the LLM prompt
        use_entity_descriptions (bool): whether to include the entity descriptions in the LLM prompt
        use_entity_synonyms (bool): whether to include the entity value's synonyms in the LLM prompt
    """

    def __init__(
            self,
            llm_name: str,
            parameters: dict = {},
            use_intent_descriptions: bool = True,
            use_training_sentences: bool = True,
            use_entity_descriptions: bool = True,
            use_entity_synonyms: bool = True
    ):
        super().__init__()
        self.llm_name: str = llm_name
        self.parameters: dict = parameters
        self.use_intent_descriptions: bool = use_intent_descriptions
        self.use_training_sentences: bool = use_training_sentences
        self.use_entity_descriptions: bool = use_entity_descriptions
        self.use_entity_synonyms: bool = use_entity_synonyms
