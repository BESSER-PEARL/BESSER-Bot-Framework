from besser.bot.core.State import State
from besser.bot.core.intent.Intent import Intent
from besser.bot.core.intent.IntentParameter import IntentParameter
from besser.bot.core.entity.Entity import Entity
from besser.bot.nlp.NLPConfiguration import NLPConfiguration
from besser.bot.library.entity.BaseEntities import ordered_base_entities, BaseEntities
from besser.bot.nlp.intent_classifier.MatchedParameter import MatchedParameter
from besser.bot.nlp.ner.base.datetime import ner_datetime, datetime_aux
from besser.bot.nlp.ner.base.number import ner_number
from besser.bot.nlp.utils import value_in_sentence, replace_value_in_sentence, find_first_temp, \
    replace_temp_value_in_sentence


def get_custom_entity_values_dict(intent, preprocessed_values=False) -> dict[str, tuple[list[IntentParameter], str]]:
    # {value/synonym: ([entity_refs], value)}
    all_entity_values: dict[str, tuple[list[IntentParameter], str]] = {}
    entity_refs_dict: dict[Entity, list[IntentParameter]] = {}
    for entity_ref in intent.parameters:
        if entity_ref.entity in entity_refs_dict:
            entity_refs_dict[entity_ref.entity].append(entity_ref)
        else:
            entity_refs_dict[entity_ref.entity] = [entity_ref]
    for entity, entity_refs in entity_refs_dict.items():
        if not entity.base_entity:
            # {value/synonym: value}
            entity_values_dict: dict[str, str] = {}
            for entity_entry in entity.entries:
                if preprocessed_values and \
                        entity_entry.preprocessed_value is not None and entity_entry.preprocessed_synonyms is not None:
                    value = entity_entry.preprocessed_value
                    synonyms = entity_entry.preprocessed_synonyms
                else:
                    value = entity_entry.value
                    synonyms = entity_entry.synonyms
                values = [value]
                values.extend(synonyms)
                for v in values:
                    if v in entity_values_dict:
                        # TODO: duplicated value in entity
                        pass
                    else:
                        entity_values_dict[v] = entity_entry.value

            for v, value in entity_values_dict.items():
                if v in all_entity_values:
                    # 2 entities have the same v
                    if all_entity_values[v][1] == value:
                        # The same value can be in different entities
                        # We order the merge of all possible references, based on the original order
                        # in the intent definition
                        v_refs = [ref for ref in intent.parameters
                                  if ref in all_entity_values[v][0] + entity_refs]
                        all_entity_values[v] = (v_refs, value)
                    else:
                        # TODO: duplicated v with different values
                        pass
                else:
                    all_entity_values[v] = (entity_refs.copy(), value)
    return all_entity_values


def base_entity_ner(sentence: str, entity_name: str, configuration: NLPConfiguration) -> tuple[str, str, dict]:
    if entity_name == BaseEntities.NUMBER:
        return ner_number(sentence, configuration)
    if entity_name == BaseEntities.DATETIME:
        result = ner_datetime(sentence, configuration)
        if result == (None, None, None):
            sentence = datetime_aux(True, sentence, configuration)
            sentence, frag, info = ner_datetime(sentence, configuration)
            if sentence is None:
                return None, None, None
            sentence = datetime_aux(False, sentence, configuration)
            result = sentence, frag, info
        return result
    if entity_name == BaseEntities.ANY:
        # return ner_any(sentence, configuration)
        return None, None, None
    return None, None, None


class SimpleNER:

    def __init__(self, nlp_engine, bot):
        self._nlp_engine = nlp_engine
        self._bot = bot

    def predict(self, state: State, message: str) -> tuple[dict[Intent, list[MatchedParameter]], dict[str, list[Intent]]]:

        ner_result: dict[Intent, list[MatchedParameter]] = {}
        intent_sentences: dict[str, list[Intent]] = {}

        for intent in state.intents:
            intent_matches: list[MatchedParameter] = []
            ner_message: str = message
            # Match custom entities
            preprocessed_values: bool
            if self._nlp_engine.configuration.stemmer:
                preprocessed_values = True
            else:
                preprocessed_values = False
            all_entity_values: dict[str, tuple[list[IntentParameter], str]] = \
                get_custom_entity_values_dict(intent, preprocessed_values)
            temps: dict[str, tuple[list[IntentParameter], str]] = {}
            temp_template = r'/temp{}/'
            temp_count = 1
            for value, (entity_refs, entry_value) in sorted(all_entity_values.items(),
                                                            key=lambda x: (len(x[0]), x[0].casefold()), reverse=True):
                # TODO: This approach doesn't allow 2 repetitions of the same value in a sentence
                # entry_value are all entry values of the entity
                # value can be an entry value (i.e. value == entry_value)
                # or a synonym of an entry value (i.e. value is a synonym of entry_value)
                # value can be preprocessed
                if value_in_sentence(value, ner_message):
                    temp_n = temp_template.format(temp_count)
                    temp_count += 1
                    ner_message = replace_value_in_sentence(ner_message, value, temp_n)
                    temps[temp_n] = (entity_refs, entry_value)

            entity_refs_done: list[IntentParameter] = []
            while len(temps) > 0:
                # We get the temp that appears first in the sentence,
                # and replace it by the 1st entity reference, in order of declaration in the bot definition
                temp = find_first_temp(ner_message)
                (entity_refs, value) = temps[temp]
                entity_ref = next(
                    (e for e in entity_refs if e not in entity_refs_done),
                    None
                )
                if entity_ref is None:
                    # We found 2 values of the same entity_ref.entity, but there can be only 1
                    ner_message = replace_temp_value_in_sentence(ner_message, temp, value)
                    # VALUE IS THE ORIGINAL (woman => Will write Femení!!!)
                else:
                    entity_refs_done.append(entity_ref)
                    ner_message = replace_temp_value_in_sentence(ner_message, temp, entity_ref.entity.name.upper())
                    intent_matches.append(MatchedParameter(entity_ref.name, value, {}))
                temps.pop(temp)

            # Match base/system entities (after custom entities)
            intent_base_entity_refs: list[IntentParameter] = [e for e in intent.parameters if
                                                              e.entity.base_entity]
            # Base entities must be checked in a specific order
            for base_entity_name in ordered_base_entities:
                for entity_ref in intent_base_entity_refs:
                    if base_entity_name == entity_ref.entity.name:
                        param_name = entity_ref.name
                        formatted_ner_sentence, formatted_frag, param_info = \
                            base_entity_ner(ner_message, base_entity_name, self._nlp_engine.configuration)
                        if formatted_ner_sentence is not None and formatted_frag is not None and param_info is not None:
                            intent_matches.append(MatchedParameter(param_name, formatted_frag, param_info))
                            ner_message = replace_value_in_sentence(formatted_ner_sentence, formatted_frag,
                                                                    base_entity_name.upper())
            matched_params_names = [mp.name for mp in intent_matches]
            for entity_param in intent.parameters:
                if entity_param.name not in matched_params_names:
                    intent_matches.append(MatchedParameter(entity_param.name, None, {}))

            ner_result[intent] = intent_matches
            if not intent_sentences.get(ner_message):
                intent_sentences[ner_message] = []
            intent_sentences[ner_message].append(intent)

        return ner_result, intent_sentences
