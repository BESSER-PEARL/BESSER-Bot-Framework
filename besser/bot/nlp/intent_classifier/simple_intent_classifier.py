from typing import TYPE_CHECKING

import numpy as np
from keras import Sequential
from keras.src.layers import TextVectorization, Dense, Embedding, GlobalAveragePooling1D
from keras.src.losses import SparseCategoricalCrossentropy
from keras.src.optimizers import Adam
from keras.src.utils import pad_sequences

from besser.bot.core.intent.intent import Intent
from besser.bot.nlp.intent_classifier.intent_classifier import IntentClassifier
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.ner.ner_prediction import NERPrediction
from besser.bot.nlp.preprocessing.text_preprocessing import process_text

if TYPE_CHECKING:
    from besser.bot.core.state import State
    from besser.bot.nlp.nlp_engine import NLPEngine


class SimpleIntentClassifier(IntentClassifier):
    """A Simple Intent Classifier.

    It works using a simple Keras Neural Network (the prediction model) for text classification.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot
        state (State): the state the intent classifier belongs to

    Attributes:
        _tokenizer (`TextVectorization <https://www.tensorflow.org/api_docs/python/tf/keras/layers/TextVectorization>`_):
            The intent classifier tokenizer
        _model (`Sequential <https://www.tensorflow.org/api_docs/python/tf/keras/Sequential>`_):
            The intent classifier language model

    See Also:
        :class:`~besser.bot.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`.
    """

    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            state: 'State'
    ):
        super().__init__(nlp_engine, state)
        self._tokenizer = TextVectorization(
            max_tokens=self._state.ic_config.num_words,
            standardize='lower_and_strip_punctuation',
            output_sequence_length=self._state.ic_config.input_max_num_tokens
        )
        self._model: Sequential = Sequential([
            Embedding(input_dim=self._state.ic_config.num_words,
                      output_dim=self._state.ic_config.embedding_dim),
            GlobalAveragePooling1D(),
            Dense(24, activation=self._state.ic_config.activation_hidden_layers),
            Dense(24, activation=self._state.ic_config.activation_hidden_layers),
            Dense(len(self._state.intents), activation=self._state.ic_config.activation_last_layer)
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

        self._tokenizer.adapt(self.__total_training_sentences)
        self.__total_training_sequences = self._tokenizer(
            self.__total_training_sentences,
        )
        self._model.compile(
            loss=SparseCategoricalCrossentropy(),
            optimizer=Adam(learning_rate=self._state.ic_config.lr),
            metrics=['accuracy']
        )

        history = self._model.fit(
            np.array(self.__total_training_sequences),
            np.array(self.__total_labels_training_sentences),
            epochs=self._state.ic_config.num_epochs, verbose=0
        )

    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        message = process_text(message, self._nlp_engine)
        intent_classifier_results: list[IntentClassifierPrediction] = []

        # We try to replace all potential entity value with the corresponding entity name
        ner_prediction: NERPrediction = self._state.bot.nlp_engine.ner.predict(self._state, message)
        for (ner_sentence, intents) in ner_prediction.ner_sentences.items():
            # DOUBLE STEMMING AVOIDED
            sentences = [ner_sentence]
            sequences = self._tokenizer(sentences)
            padded = pad_sequences(
                sequences,
                maxlen=self._state.ic_config.input_max_num_tokens,
                padding='post',
                truncating='post'
            )
            run_full_prediction: bool = True
            if self._state.ic_config.discard_oov_sentences and all(i in [0, 1] for i in sequences[0]):
                # The sentence to predict consists of only out of vocabulary tokens,
                # so we can automatically assign a zero probability to all classes
                prediction = np.zeros(len(self._state.intents))
                run_full_prediction = False  # no need to go ahead with the full NN-based prediction
            elif self._state.ic_config.check_exact_prediction_match:
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
