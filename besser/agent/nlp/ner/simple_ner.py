from typing import TYPE_CHECKING

from besser.agent import nlp
from besser.agent.core.entity.entity import Entity
from besser.agent.core.intent.intent import Intent
from besser.agent.core.intent.intent_parameter import IntentParameter
from besser.agent.core.state import State
from besser.agent.library.entity.base_entities import BaseEntities, ordered_base_entities
from besser.agent.nlp.ner.base.datetime import ner_datetime
from besser.agent.nlp.ner.base.number import ner_number
from besser.agent.nlp.ner.matched_parameter import MatchedParameter
from besser.agent.nlp.ner.ner import NER
from besser.agent.nlp.ner.ner_prediction import NERPrediction
from besser.agent.nlp.utils import find_first_temp, replace_temp_value_in_sentence, replace_value_in_sentence, \
    value_in_sentence

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.core.state import State
    from besser.agent.nlp.nlp_engine import NLPEngine


def get_custom_entity_values_dict(
        intent: Intent,
        processed_values: bool = False
) -> dict[str, tuple[list[IntentParameter], str]]:
    """
    Get a dictionary containing, for each entity value `v` (including synonyms) among all paramters in an intent,
    a tuple with: 1 - the intent parameters where `v` could be a match and 2 - the main value of `v` (if `v` is not a
    synonym and it is the main value, it will be duplicated):

    {value/synonym: ([intent_parameters], value)}

    Args:
        intent (Intent): the target intent
        processed_values (bool): whether to retrieve the entities processed values or not

    Returns:
        dict[str, tuple[list[IntentParameter], str]]: the dictionary
    """
    all_entity_values: dict[str, tuple[list[IntentParameter], str]] = {}
    intent_parameters_dict: dict[Entity, list[IntentParameter]] = {}
    for intent_parameter in intent.parameters:
        if intent_parameter.entity in intent_parameters_dict:
            intent_parameters_dict[intent_parameter.entity].append(intent_parameter)
        else:
            intent_parameters_dict[intent_parameter.entity] = [intent_parameter]
    for entity, intent_parameters in intent_parameters_dict.items():
        if not entity.base_entity:
            # {value/synonym: value}
            entity_values_dict: dict[str, str] = {}
            for entity_entry in entity.entries:
                if processed_values and \
                        entity_entry.processed_value is not None and entity_entry.processed_synonyms is not None:
                    value = entity_entry.processed_value
                    synonyms = entity_entry.processed_synonyms
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
                                  if ref in all_entity_values[v][0] + intent_parameters]
                        all_entity_values[v] = (v_refs, value)
                    else:
                        # TODO: duplicated v with different values
                        pass
                else:
                    all_entity_values[v] = (intent_parameters.copy(), value)
    return all_entity_values


def base_entity_ner(
        sentence: str,
        entity_name: str,
        nlp_engine: 'NLPEngine'
) -> tuple[str or None, str or None, dict or None]:
    """
    Do NER with a base entity.

    Given a sentence and a base entity, look for a value of the base entity in the sentence.

    Args:
        sentence (str): the text to do the NER to
        entity_name (str): the base entity name
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent

    Returns:
        tuple[str or None, str or None, dict or None]: the sentence (that can be modified), the matched fragment,
            and the extra info. If no value has been found, return None
    """
    if entity_name == BaseEntities.NUMBER.value:
        return ner_number(sentence, nlp_engine)
    if entity_name == BaseEntities.DATETIME.value:
        return ner_datetime(sentence, nlp_engine)
    if entity_name == BaseEntities.ANY.value:
        # return ner_any(sentence, configuration)
        return None, None, None
    return None, None, None


class SimpleNER(NER):
    """A simple NER.

    It can find an entity value in a user message only with exact matching (i.e. slight variations on an entity value
    within a user message will make the NER fail)

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
        agent (Agent): the agent the NER belongs to
    """
    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            agent
    ):
        super().__init__(nlp_engine, agent)

    def train(self) -> None:
        for entity in self._agent.entities:
            entity.process_entity_entries(self._nlp_engine)

    def predict(self, state: State, message: str) -> NERPrediction:
        ner_prediction: NERPrediction = NERPrediction()
        for intent in state.intents:
            intent_matches: list[MatchedParameter] = []
            ner_sentence: str = message
            # Match custom entities
            processed_values: bool
            pre_processing = self._nlp_engine.get_property(nlp.NLP_PRE_PROCESSING)
            if pre_processing:
                # Other conditions may be necessary to use the processed entity values
                processed_values = True
            else:
                processed_values = False
            all_entity_values: dict[str, tuple[list[IntentParameter], str]] = \
                get_custom_entity_values_dict(intent, processed_values)
            temps: dict[str, tuple[list[IntentParameter], str]] = {}
            temp_template = r'/temp{}/'
            temp_count = 1
            for value, (intent_parameters, entry_value) in sorted(all_entity_values.items(),
                                                            key=lambda x: (len(x[0]), x[0].casefold()), reverse=True):
                # TODO: This approach doesn't allow 2 repetitions of the same value in a sentence
                # entry_value are all entry values of the entity
                # value can be an entry value (i.e. value == entry_value)
                # or a synonym of an entry value (i.e. value is a synonym of entry_value)
                # value can be processed
                if value_in_sentence(value, ner_sentence):
                    temp_n = temp_template.format(temp_count)
                    temp_count += 1
                    ner_sentence = replace_value_in_sentence(ner_sentence, value, temp_n)
                    temps[temp_n] = (intent_parameters, entry_value)

            intent_parameters_done: list[IntentParameter] = []
            while len(temps) > 0:
                # We get the temp that appears first in the sentence,
                # and replace it by the 1st entity reference, in order of declaration in the agent definition
                temp = find_first_temp(ner_sentence)
                (intent_parameters, value) = temps[temp]
                intent_parameter = next(
                    (e for e in intent_parameters if e not in intent_parameters_done),
                    None
                )
                if intent_parameter is None:
                    # We found 2 values of the same intent_parameter.entity, but there can be only 1
                    ner_sentence = replace_temp_value_in_sentence(ner_sentence, temp, value)
                    # VALUE IS THE ORIGINAL (woman => Will write Femení!!!)
                else:
                    intent_parameters_done.append(intent_parameter)
                    ner_sentence = replace_temp_value_in_sentence(ner_sentence, temp, intent_parameter.entity.name.upper())
                    intent_matches.append(MatchedParameter(intent_parameter.name, value, {}))
                temps.pop(temp)

            # Match base/system entities (after custom entities)
            base_entity_intent_parameters: list[IntentParameter] = [e for e in intent.parameters if
                                                              e.entity.base_entity]
            # Base entities must be checked in a specific order
            for base_entity_name in ordered_base_entities:
                for intent_parameter in base_entity_intent_parameters:
                    if base_entity_name.value == intent_parameter.entity.name:
                        param_name = intent_parameter.name
                        formatted_ner_sentence, formatted_frag, param_info = \
                            base_entity_ner(ner_sentence, base_entity_name.value, self._nlp_engine)
                        if formatted_ner_sentence is not None and formatted_frag is not None and param_info is not None:
                            intent_matches.append(MatchedParameter(param_name, formatted_frag, param_info))
                            ner_sentence = replace_value_in_sentence(formatted_ner_sentence, formatted_frag,
                                                                    base_entity_name.value.upper())
            matched_params_names = [mp.name for mp in intent_matches]
            for entity_param in intent.parameters:
                if entity_param.name not in matched_params_names:
                    intent_matches.append(MatchedParameter(entity_param.name, None, {}))

            ner_prediction.add_intent_matched_parameters(intent, intent_matches)
            ner_prediction.add_ner_sentence(ner_sentence, intent)

        return ner_prediction
