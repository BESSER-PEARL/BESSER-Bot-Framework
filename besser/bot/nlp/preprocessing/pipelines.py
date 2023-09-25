import logging

import nltk
import snowballstemmer as SnowballStemmer

lang_map_stemmers = SnowballStemmer._languages
lang_map_tokenizers = nltk.SnowballStemmer.languages
lang_map = {
    'en': 'english',
    'es': 'spanish',
    'fr': 'french',
    'it': 'italian',
    'de': 'german',
    'nl': 'dutch',
    'pt': 'portuguese',
    'ca': 'catalan',
    'lb': 'luxembourgish'
}
stemmers: dict[str, SnowballStemmer.stemmer] = {}

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    # "punkt" is not installed, download it
    nltk.download('punkt')


def create_or_get_stemmer(lang: str = 'english') -> SnowballStemmer:
    if lang in stemmers:
        return stemmers[lang]
    stemmer = SnowballStemmer.stemmer(lang)
    stemmers[lang] = stemmer
    logging.info(f'Stemmer added: {lang}')
    return stemmer
