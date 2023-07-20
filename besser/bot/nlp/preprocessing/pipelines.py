import logging

import nltk
from nltk.stem import SnowballStemmer

lang_map = {
    'en': 'english',
    'es': 'spanish',
    'fr': 'french',
    'it': 'italian',
    'de': 'german',
    'nl': 'dutch',
    'pt': 'portuguese',
    'ca': 'catalan'
}

stemmers: dict[str, SnowballStemmer] = {}

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    # "punkt" is not installed, download it
    nltk.download('punkt')


def create_or_get_stemmer(lang: str = 'english') -> SnowballStemmer:
    if lang in stemmers:
        return stemmers[lang]
    stemmer = SnowballStemmer(lang)
    stemmers[lang] = stemmer
    logging.info(f'Stemmer added: {lang}')
    return stemmer
