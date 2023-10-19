import os
from typing import TYPE_CHECKING

import keras
import numpy as np
from keras import Sequential
from keras.layers import Dense, Embedding, GlobalAveragePooling1D
from keras.losses import SparseCategoricalCrossentropy
from keras.preprocessing.text import Tokenizer
from keras.utils import pad_sequences

from besser.bot.core.intent.intent import Intent
from besser.bot.core.state import State
from besser.bot.nlp.intent_classifier.intent_classifier import IntentClassifier
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.ner.ner_prediction import NERPrediction
from besser.bot.nlp.preprocessing.text_preprocessing import process_text

if TYPE_CHECKING:
    from besser.bot.nlp.nlp_engine import NLPEngine

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class SimpleIntentClassifier(IntentClassifier):
    """A Simple Intent Classifier.

    It works using a simple Keras Neural Network (the prediction model) for text classification.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot
        state (State): the state the intent classifier belongs to

    Attributes:
        _tokenizer (`Tokenizer <https://www.tensorflow.org/api_docs/python/tf/keras/preprocessing/text/Tokenizer>`_):
            The intent classifier tokenizer
        _model (`Sequential <https://www.tensorflow.org/api_docs/python/tf/keras/Sequential>`_):
            The intent classifier language model
        num_words (int): Max num of words to keep in the index of words
        lower (bool): Weather to transform the sentences to lowercase or not
        oov_token (str): Token for the out of vocabulary words
        num_epochs (int): Number of epochs to be run during training
        embedding_dim (int): Number of embedding dimensions to be used when embedding the words
        input_max_num_tokens (int): Max length for the vector representing a sentence
        discard_oov_sentences (bool): Weather to automatically assign zero probabilities to sentences with all tokens
            being oov ones or not
        check_exact_prediction_match (bool): Whether to check for exact match between the sentence to predict and one of
            the training sentences or not
        activation_last_layer (str): The activation function of the last layer
        activation_hidden_layers (str): The activation function of the hidden layers
        lr (float): Learning rate for the optimizer
    """

    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            state: State
    ):
        super().__init__(nlp_engine, state)
        self.num_words: int = 1000
        self.lower: bool = True
        self.oov_token: str = '<OOV>'
        self.num_epochs: int = 300
        self.embedding_dim: int = 128
        self.input_max_num_tokens: int = 15
        self.discard_oov_sentences: bool = True
        self.check_exact_prediction_match: bool = True
        self.activation_last_layer: str = 'sigmoid'
        self.activation_hidden_layers: str = 'tanh'
        self.lr: float = 0.001

        self._tokenizer: Tokenizer = Tokenizer(
            num_words=self.num_words,
            lower=self.lower,
            oov_token=self.oov_token
        )
        self._model: Sequential = Sequential([
            Embedding(input_dim=self.num_words,
                      output_dim=self.embedding_dim,
                      input_length=self.input_max_num_tokens),
            GlobalAveragePooling1D(),
            Dense(24, activation=self.activation_hidden_layers),
            Dense(24, activation=self.activation_hidden_layers),
            Dense(len(self._state.intents), activation=self.activation_last_layer)
        ])
        self.__total_training_sentences: list[str] = []
        """All the processed training sentences of all intents of the intent classifier's state."""

        self.__total_training_sequences: list[str] = []
        """All the training sequences of all intents of the intent classifier's state."""

        self.__total_labels_training_sentences: list[int] = []
        """The label (identifying the intent) of all training sentences."""

        self.__intent_label_mapping: dict[int, Intent] = {}
        """A mapping of the intent labels and their corresponding intents."""

    def train(self) -> None:
        for intent in self._state.intents:
            intent.process_training_sentences(self._nlp_engine)
            index_intent = self._state.intents.index(intent)
            self.__total_training_sentences.extend(
                intent.processed_training_sentences
            )
            self.__total_labels_training_sentences.extend(
                [index_intent for _ in range(len(intent.processed_training_sentences))]
            )
            self.__intent_label_mapping[index_intent] = intent

        self._tokenizer.fit_on_texts(self.__total_training_sentences)
        self.__total_training_sequences = pad_sequences(
            self._tokenizer.texts_to_sequences(self.__total_training_sentences),
            maxlen=self.input_max_num_tokens,
            padding='post',
            truncating='post'
        )

        self._model.compile(
            loss=SparseCategoricalCrossentropy(),
            optimizer=keras.optimizers.Adam(learning_rate=self.lr),
            metrics=['accuracy']
        )

        history = self._model.fit(
            np.array(self.__total_training_sequences),
            np.array(self.__total_labels_training_sentences),
            epochs=self.num_epochs, verbose=0
        )

    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        message = process_text(message, self._nlp_engine)
        intent_classifier_results: list[IntentClassifierPrediction] = []

        # We try to replace all potential entity value with the corresponding entity name
        ner_prediction: NERPrediction = self._state.bot.nlp_engine.ner.predict(self._state, message)
        for (ner_sentence, intents) in ner_prediction.ner_sentences.items():
            # DOUBLE STEMMING AVOIDED
            sentences = [ner_sentence]
            sequences = self._tokenizer.texts_to_sequences(sentences)
            padded = pad_sequences(
                sequences,
                maxlen=self.input_max_num_tokens,
                padding='post',
                truncating='post'
            )
            run_full_prediction: bool = True
            if self.discard_oov_sentences and all(i == 1 for i in sequences[0]):
                # The sentence to predict consists of only out of vocabulary tokens,
                # so we can automatically assign a zero probability to all classes
                prediction = np.zeros(len(self._state.intents))
                run_full_prediction = False  # no need to go ahead with the full NN-based prediction
            elif self.check_exact_prediction_match:
                # We check if there is an exact match with one of the training sentences
                for i, training_sequence in enumerate(self.__total_training_sequences):
                    intent_label = self.__total_labels_training_sentences[i]
                    if np.array_equal(padded[0], training_sequence)\
                            and self.__intent_label_mapping[intent_label] in intents:
                        run_full_prediction = False
                        # We set to 1 the corresponding intent with full confidence and to zero all the
                        prediction = np.zeros(len(self._state.intents))
                        np.put(prediction, intent_label, 1.0, mode='raise')
                        # We don't check if there is more than one intent that could be the exact match
                        # as this would be an inconsistency in the bot definition anyway
                        break

            if run_full_prediction:
                full_prediction = self._model.predict(padded, verbose=0)
                # We return just a single array with the predictions as we predict for just one sentence
                prediction = full_prediction[0]

            for intent in intents:
                # It is impossible to have a duplicated intent in another ner_sentence
                intent_index = self._state.intents.index(intent)
                intent_classifier_results.append(IntentClassifierPrediction(
                    intent,
                    prediction[intent_index],
                    ner_sentence,
                    ner_prediction.intent_matched_parameters[intent]
                ))

        return intent_classifier_results
