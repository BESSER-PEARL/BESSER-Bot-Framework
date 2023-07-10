import re


def value_in_sentence(value: str, sentence: str) -> bool:
    regex = re.compile(r'\b' + re.escape(value) + r'\b', re.IGNORECASE)
    return value.lower() == sentence.lower() or (regex.search(sentence) is not None)


def replace_value_in_sentence(sentence: str, frag: str, repl: str) -> str:
    if sentence.lower() == frag.lower():
        return repl
    if frag[0] == '-':
        # Necessary to replace negative numbers properly
        regex = re.compile(re.escape(frag) + r'\b', re.IGNORECASE)
    else:
        regex = re.compile(r'\b' + re.escape(frag) + r'\b', re.IGNORECASE)
    return regex.sub(repl=repl, string=sentence, count=1)


def replace_temp_value_in_sentence(sentence: str, frag: str, repl: str) -> str:
    regex = re.compile(frag, re.IGNORECASE)
    return regex.sub(repl=repl, string=sentence, count=1)


def find_first_temp(sentence: str) -> str:
    regex = re.compile(r'/temp[0-9]+/')
    return regex.search(sentence).group()
