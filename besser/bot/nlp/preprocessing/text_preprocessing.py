from nltk.tokenize import word_tokenize
from besser.bot.core.intent.intent import Intent
from besser.bot.nlp.nlp_configuration import NLPConfiguration
from besser.bot.core.entity.entity import Entity
from besser.bot.nlp.preprocessing.pipelines import lang_map, create_or_get_stemmer
from besser.bot.nlp.utils import replace_value_in_sentence


def preprocess_text(text: str, configuration: NLPConfiguration) -> str:
    preprocessed_sentence: str = text
    preprocessed_sentence = preprocessed_sentence.replace('_', ' ')
    if configuration.stemmer:
        # TODO: remove punctuation signs
        preprocessed_sentence = stem_text(preprocessed_sentence, configuration)
    return preprocessed_sentence


def preprocess_custom_entity_entries(entity: Entity, configuration: NLPConfiguration):
    for entry in entity.entries:
        entry.processed_value = preprocess_text(entry.value, configuration)
        entry.processed_synonyms = []
        for synonym in entry.synonyms:
            entry.processed_synonyms.append(preprocess_text(synonym, configuration))


def preprocess_training_sentences(intent: Intent, configuration: NLPConfiguration):
    intent.processed_training_sentences = []
    for i in range(len(intent.training_sentences)):
        preprocessed_sentence: str = intent.training_sentences[i]

        if configuration.use_ner_in_prediction:
            preprocessed_sentence = replace_ner_in_training_sentence(preprocessed_sentence, intent, configuration)

        preprocessed_sentence = preprocess_text(preprocessed_sentence, configuration)

        intent.processed_training_sentences.append(preprocessed_sentence)


def replace_ner_in_training_sentence(sentence: str, intent: Intent, configuration: NLPConfiguration):
    ner_sentence: str = sentence
    for entity_ref in intent.parameters:
        ner_sentence = replace_value_in_sentence(ner_sentence, entity_ref.fragment, entity_ref.entity.name.upper())
    return ner_sentence


def stem_text(text: str, configuration: NLPConfiguration) -> str:
    tokens: list[str] = word_tokenize(text, language='english')
    # print(Stemmer.algorithms()) # Names of the languages supported by the stemmer
    stemmer_language: str = 'en'
    if configuration.country in lang_map:
        stemmer_language = lang_map[configuration.country]

    stemmer = create_or_get_stemmer(stemmer_language)
    stemmed_sentence: list[str] = []

    # We stem words one by one to be able to skip words all in uppercase (e.g. references to entity types)
    for word in tokens:
        stemmed_word: str = word
        if not word.isupper():
            stemmed_word = stemmer.stem(word)
        stemmed_sentence.append(stemmed_word)

    # stemmed_sentence: list[str] = stemmer.stemWords(tokens)
    # print("Stemmed sentence")
    # print(stemmed_sentence)
    joined_string = ' '.join([str(item) for item in stemmed_sentence])
    return joined_string
