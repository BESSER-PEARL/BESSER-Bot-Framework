import re

from text_to_num import alpha2digit

from besser.bot.nlp.nlp_configuration import NLPConfiguration


def ner_number(sentence: str, configuration: NLPConfiguration) -> tuple[str, str, dict]:
    # First, we parse any number in the sentence expressed in natural language (e.g. "five") to actual numbers
    sentence = alpha2digit(sentence, lang=configuration.country)

    # Negative/positive numbers with optional point/comma followed by more digits
    regex = re.compile(r'(\b|[-+])\d+\.?\d*([.,]\d+)?\b')
    search = regex.search(sentence)
    if search is None:
        return None, None, None
    matched_frag = search.group(0)
    formatted_frag = matched_frag.replace(',', '.').replace('+', '')
    sentence = sentence[:search.span(0)[0]] + formatted_frag + sentence[search.span(0)[1]:]
    return sentence, formatted_frag, {}
