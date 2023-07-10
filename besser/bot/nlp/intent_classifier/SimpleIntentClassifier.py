import numpy as np

from keras import Sequential
from keras.layers import Embedding, GlobalAveragePooling1D, Dense
from keras.losses import SparseCategoricalCrossentropy
from keras.preprocessing.text import Tokenizer
from keras.utils import pad_sequences

from besser.bot.core.intent.Intent import Intent
from besser.bot.nlp.intent_classifier.IntentClassifierPrediction import IntentClassifierPrediction
from besser.bot.nlp.intent_classifier.MatchedParameter import MatchedParameter
from besser.bot.nlp.preprocessing.text_preprocessing import preprocess_training_sentences


class SimpleIntentClassifier:

    def __init__(self, nlp_engine, state):
        self.nlp_engine = nlp_engine
        self.state = state
        self.tokenizer = None
        self.model = None

    def train(self):
        if not self.state.intents:
            return
        self.tokenizer = Tokenizer(num_words=self.nlp_engine.configuration.num_words,
                                   lower=self.nlp_engine.configuration.lower,
                                   oov_token=self.nlp_engine.configuration.oov_token)
        self.model = Sequential([
            Embedding(input_dim=self.nlp_engine.configuration.num_words,
                      output_dim=self.nlp_engine.configuration.embedding_dim,
                      input_length=self.nlp_engine.configuration.input_max_num_tokens),
            GlobalAveragePooling1D(),
            Dense(24, activation=self.nlp_engine.configuration.activation_hidden_layers),
            # tanh is also a valid alternative for these intermediate layers
            Dense(24, activation=self.nlp_engine.configuration.activation_hidden_layers),
            Dense(len(self.state.intents), activation=self.nlp_engine.configuration.activation_last_layer)
            # choose sigmoid if, in your scenario, a sentence could possibly match several intents
        ])

        total_training_sentences: list[str] = []
        total_training_sequences: list[str]
        total_labels_training_sentences: list[int] = []

        for intent in self.state.intents:
            preprocess_training_sentences(intent, self.nlp_engine.configuration)
            index_intent = self.state.intents.index(intent)
            total_training_sentences.extend(intent.processed_training_sentences)
            total_labels_training_sentences.extend(
                [index_intent for _ in range(len(intent.processed_training_sentences))])

        self.tokenizer.fit_on_texts(total_training_sentences)
        total_training_sequences = pad_sequences(self.tokenizer.texts_to_sequences(total_training_sentences),
                                                 padding='post', truncating='post',
                                                 maxlen=self.nlp_engine.configuration.input_max_num_tokens)

        self.model.compile(loss=SparseCategoricalCrossentropy(), optimizer='adam', metrics=['accuracy'])

        # print("Model summary: ")
        # model.summary()

        # np conversion is needed to get it to work with TensorFlow 2.x
        history = self.model.fit(np.array(total_training_sequences), np.array(total_labels_training_sentences),
                                 epochs=self.nlp_engine.configuration.num_epochs, verbose=0)

        # plot_training_graphs_without_validation(history, "accuracy")
        # plot_training_graphs_without_validation(history, "loss")

    def predict(self, message: str) -> list[IntentClassifierPrediction]:

        intent_classifier_results: list[IntentClassifierPrediction] = []
        ner_result: dict[Intent, list[MatchedParameter]] = {}
        intent_sentences: dict[str, list[Intent]] = {}

        # We try to replace all potential entity value with the corresponding entity name
        ner_result, intent_sentences = self.state.bot.nlp_engine.ner.predict(message)

        for (ner_sentence, intents) in intent_sentences.items():
            # DOUBLE STEMMING AVOIDED
            sentences = [ner_sentence]
            sequences = self.tokenizer.texts_to_sequences(sentences)
            padded = pad_sequences(sequences, padding='post',
                                   maxlen=self.nlp_engine.configuration.input_max_num_tokens,
                                   truncating='post')
            run_full_prediction: bool = True
            if self.nlp_engine.configuration.discard_oov_sentences and all(i == 1 for i in sequences[0]):
                # the sentence to predict consists of only out of vocabulary tokens so we can automatically assign a zero probability to all classes
                prediction = np.zeros(len(self.state.intents))
                run_full_prediction = False  # no need to go ahead with the full NN-based prediction
            elif self.nlp_engine.configuration.check_exact_prediction_match:
                found: bool = False
                found_intent: int
                i: int = 0
                """
                for training_sequence in context.training_sequences:
                    if np.array_equal(padded[0], training_sequence):
                        found = True
                        found_intent = context.training_labels[i]
                        run_full_prediction = False
                        break
                    i += 1
                if found:
                    # We set to true the corresponding intent with full confidence and to zero all the
                    # We don't check if there is more than one intent that could be the exact match as this would be an inconsistency in the bot definition anyways
                    prediction = np.zeros(len(context.intent_refs))
                    np.put(prediction, found_intent, 1.0, mode='raise')
                """

            if run_full_prediction:
                full_prediction = self.model.predict(padded, verbose=0)
                prediction = full_prediction[
                    0]  # We return just a single array with the predictions as we predict for just one sentence

            for intent in intents:
                # it is impossible to have a duplicated intent in another ner_sentence
                intent_index = self.state.intents.index(intent)
                intent_classifier_results.append(
                    IntentClassifierPrediction(intent, prediction[intent_index], ner_sentence, ner_result[intent]))

        return intent_classifier_results
