from besser.bot.core.property import Property

# Definition of the bot properties within the nlp section

SECTION_NLP = 'nlp'

NLP_LANGUAGE = Property(SECTION_NLP, 'nlp.language', str, 'en')
NLP_REGION = Property(SECTION_NLP, 'nlp.region', str, 'US')
NLP_TIMEZONE = Property(SECTION_NLP, 'nlp.timezone', str, 'Europe/Madrid')
NLP_STEMMER = Property(SECTION_NLP, 'nlp.stemmer', bool, True)
NLP_INTENT_THRESHOLD = Property(SECTION_NLP, 'nlp.intent_threshold', float, 0.4)
