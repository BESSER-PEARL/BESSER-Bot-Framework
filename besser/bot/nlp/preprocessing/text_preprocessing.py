from typing import TYPE_CHECKING
from nltk.tokenize import word_tokenize

from besser.bot import nlp
from besser.bot.nlp.preprocessing.pipelines import create_or_get_stemmer, lang_map, lang_map_tokenizers

if TYPE_CHECKING:
    from besser.bot.nlp.nlp_engine import NLPEngine


def process_text(text: str, nlp_engine: 'NLPEngine') -> str:
    pre_processing: bool = nlp_engine.get_property(nlp.NLP_PRE_PROCESSING)
    language: str = nlp_engine.get_property(nlp.NLP_LANGUAGE)

    preprocessed_sentence: str = text
    # preprocessed_sentence = preprocessed_sentence.replace('_', ' ')
    if pre_processing:
        # TODO: remove punctuation signs
        if language != "lb":
            preprocessed_sentence = stem_text(preprocessed_sentence, language)
        else:
            # as luxembourgish is the only time we use a lemmatize, we decided to go with the
            # easy path to just make one exception
            preprocessed_sentence = lemmatize_lux_text(preprocessed_sentence)
    return preprocessed_sentence


def stem_text(text: str, language: str) -> str:
    stemmer_language: str = 'english'  # default set to english
    if language in lang_map:
        stemmer_language = lang_map[language]
    stemmer = create_or_get_stemmer(stemmer_language)
    # not every stemming language has a corresponsing tokenizer, should we simply use a basic tokenizer for languages that do not possess the fitting tokenizer?
    if language in lang_map_tokenizers:
        tokens: list[str] = word_tokenize(text, language=stemmer_language)
    else:
        tokens: list[str] = text.split()
    stemmed_sentence: list[str] = []
    # We stem words one by one to be able to skip words all in uppercase (e.g. references to entity types)
    for word in tokens:
        stemmed_word: str = word
        if not word.isupper():
            stemmed_word = stemmer.stemWord(word)
        stemmed_sentence.append(stemmed_word)

    joined_string = ' '.join([str(item) for item in stemmed_sentence])
    return joined_string


def lemmatize_lux_text(text: str) -> str:
    import spellux
    from spacy.lang.lb import Luxembourgish

    nlp = Luxembourgish()
    doc = nlp(text)
    tokens = []
    for token in doc: 
        tokens.append(token.text)
    lemmatized_sentence: list[str] = []
    # We lemmatize words one by one to be able to skip words all in uppercase (e.g. references to entity types)
    for word in tokens:
        lemmatized_word: str = word
        if not word.isupper():
            lemmatized_word = spellux.lemmatize_text([word], sim_ratio=0.8)[0]
        lemmatized_sentence.append(lemmatized_word)
    joined_string = ' '.join([str(item) for item in lemmatized_sentence])
    return joined_string
