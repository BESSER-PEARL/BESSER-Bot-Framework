from besser.bot.core.intent.intent import Intent
from besser.bot.nlp.intent_classifier.matched_parameter import MatchedParameter


class NERPrediction:

    def __init__(self):
        self.intent_matched_parameters: dict[Intent, list[MatchedParameter]] = {}
        self.ner_sentences: dict[str, list[Intent]] = {}

    def add_intent_matched_parameters(self, intent: Intent, intent_matches: list[MatchedParameter]):
        self.intent_matched_parameters[intent] = intent_matches

    def add_ner_sentence(self, ner_sentence: str, intent: Intent):
        if ner_sentence not in self.ner_sentences:
            self.ner_sentences[ner_sentence] = []
        self.ner_sentences[ner_sentence].append(intent)
