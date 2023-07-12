class NLPConfiguration:

    def __init__(self, country: str = "en", region: str = "US", timezone: str = 'Europe/Madrid', numwords: int = 1000,
                 lower: bool = True, oov_token="<OOV>",
                 num_epochs: int = 300, embedding_dim: int = 128, input_max_num_tokens: int = 15, stemmer: bool = True,
                 discard_oov_sentences=True, check_exact_prediction_match=True,
                 use_ner_in_prediction=True, activation_last_layer="sigmoid", activation_hidden_layers="tanh",
                 lr=0.001):
        self.country = country
        self.region = region
        self.timezone = timezone # The timezone to use
        self.num_words = numwords  # max num of words to keep in the index of words
        self.lower = lower  # transform sentences to lowercase
        self.oov_token = oov_token  # token for the out of vocabulary words
        self.num_epochs = num_epochs # Number of epochs to be run during training
        self.embedding_dim = embedding_dim # Number of embedding dimensions to be used when embedding the words
        self.input_max_num_tokens = input_max_num_tokens  # max length for the vector representing a sentence
        self.stemmer = stemmer  # whether to use a stemmer
        self.discard_oov_sentences = discard_oov_sentences  # Automatically assign zero probabilities to sentences with all tokens being oov ones
        self.check_exact_prediction_match = check_exact_prediction_match  # whether to check for exact match between the sentence to predict and one of the training sentences
        self.use_ner_in_prediction = use_ner_in_prediction  # whether to use NER in the prediction
        self.activation_last_layer = activation_last_layer # The activation function of the last layer
        self.activation_hidden_layers = activation_hidden_layers # The activation function of the hidden layers
        self.lr = lr # Learning rate for the optimizer
