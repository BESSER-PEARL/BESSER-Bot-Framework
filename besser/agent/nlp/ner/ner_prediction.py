from besser.agent.core.intent.intent import Intent
from besser.agent.nlp.ner.matched_parameter import MatchedParameter


class NERPrediction:
    """The prediction result of the NER.

    Attributes:
        intent_matched_parameters (dict[Intent, list[MatchedParameter]]): For each intent, the list of matched
            parameters
        ner_sentences (dict[str, list[Intent]]): After NER, the original sentence is modified by replacing the found
            values by the entity names. Therefore, some resulting sentences may be identical. This dict contains an
            entry for each different sentence and the list of intents for which, after doing NER in the
            original sentence, that is the resulting sentence.
    """
    def __init__(self):
        self.intent_matched_parameters: dict[Intent, list[MatchedParameter]] = {}
        self.ner_sentences: dict[str, list[Intent]] = {}

    def add_intent_matched_parameters(self, intent: Intent, intent_matches: list[MatchedParameter]) -> None:
        """Add a list of matched parameters to a specific intent.

        Args:
            intent (Intent): the intent to add the matched parameters
            intent_matches (list[MatchedParameter]): the list of mathched parameters to add to the intent
        """
        self.intent_matched_parameters[intent] = intent_matches

    def add_ner_sentence(self, ner_sentence: str, intent: Intent) -> None:
        """Store a NER sentence and its corresponding intent.

        Args:
            ner_sentence (str): the sentence after NER
            intent (Intent): the intent for which, after NER, the original sentence has become `ner_sentence`

        Returns:

        """
        if ner_sentence not in self.ner_sentences:
            self.ner_sentences[ner_sentence] = []
        self.ner_sentences[ner_sentence].append(intent)
