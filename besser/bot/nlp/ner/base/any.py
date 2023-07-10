from besser.bot.nlp.NLPConfiguration import NLPConfiguration


def ner_any(sentence: str, configuration: NLPConfiguration) -> tuple[str, str, dict]:
    return sentence, sentence, {}
