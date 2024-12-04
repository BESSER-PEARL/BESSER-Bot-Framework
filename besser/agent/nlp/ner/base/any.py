from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.nlp.nlp_engine import NLPEngine


def ner_any(sentence: str, nlp_engine: 'NLPEngine') -> tuple[str, str, dict]:
    return sentence, sentence, {}
