import json
import logging
import os
import traceback
from typing import TYPE_CHECKING

import replicate
import requests
from openai import OpenAI
from transformers import pipeline

from besser.bot import nlp
from besser.bot.nlp import NLP_LANGUAGE
from besser.bot.nlp.intent_classifier.intent_classifier import IntentClassifier
from besser.bot.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.ner.matched_parameter import MatchedParameter
from besser.bot.nlp.utils import find_json

if TYPE_CHECKING:
    from besser.bot.core.state import State
    from besser.bot.nlp.nlp_engine import NLPEngine


class LLMIntentClassifier(IntentClassifier):
    """An LLM-based Intent Classifier.

    It sends a prompt to an LLM, indicating how to perform the Intent Classification task and providing the State's
    intents and its parameters

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot
        state (State): the state the intent classifier belongs to

    Attributes:


    See Also:
        :class:`~besser.bot.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`.
    """

    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            state: 'State'
    ):
        super().__init__(nlp_engine, state)
        self.__intents_dict: dict = {}
        self.__entities_dict: dict = {}

    def _generate_prompt(self, message: str) -> str:
        """Generates the prompt for the LLM giving instructions for the intent classification task.

        Args:
            message (str): the user message on which the LLM must detect the intent

        Returns:
            str: the generated prompt
        """
        example_output = {
            'intent1': {
                'score': 0.7,
                'parameters': {
                    'param1': 'value1',
                    'param2': 'value2'
                }
            }
        }

        prompt = \
f"""
You are a helpful assistant. Your task is to recognize the intent of a sentence, together with its
parameters (if any). Therefore, you must work on 2 different problems: text classification and
named entity recognition. This is the definition of training data you will have in order to solve the
problem:

For each intent:

{'- A brief description of its purpose'
if self._state.ic_config.use_intent_descriptions else ''}
{'- A set of training sentences, that you must take as examples of what the user message should look like.'
'  Note that the similarity between a message and the training sentences can exist in terms of'
'  orthographic similarity (i.e. common or similar words) and semantic similarity (with similar meanings)'
if self._state.ic_config.use_training_sentences else ''}
- Some intents may have parameters. You will also have them. Each parameter is composed by a name,
{'  an entity and a fragment. The fragment is the part of the training sentences where the parameters are expected to be.'
'  In the training sentences, the words with all characters uppercased (e.g. CITY) probably belong to intent parameters (their fragments).'
if self._state.ic_config.use_training_sentences else '  and an entity.'} Finding parameters in the message may be hints to detect its intent as well.

For each entity:

{'- A brief description of its purpose'
if self._state.ic_config.use_entity_descriptions else ''}
- All the values associated to the entity (if any).
{'- For each value, there may be a list of synonyms. Use them as a reference, but if you find one in the'
'  user message, always get the "main" value'
if self._state.ic_config.use_entity_synonyms else ''}
A special kind of entities, called base entities, have no values associated. They can match any value of its
category. For example, the base entity 'number' can match any number in a sentence.

Notes:

- A parameter may be explicit in the message, but also implicit. If you think the message
contains an entity (even if it is implicit), add it to the result.
- If you find a parameter in the message whose entity has associated values, but the found value is not
present there (i.e. it may be a synonym), you must replace it by the appropriate entity value. Never write
an entity value's synonym
- You cannot assign a parameter to an intent if it is not part of the intent definition.
- It is also possible to recognize an intent when there is some of its parameter missing (even though it is
not a good sign).
- The message may not belong to any intent. When you think so, score the intents properly.
- This is the language of the training data (ISO 639-1 format): '{self._nlp_engine.get_property(NLP_LANGUAGE)}'

Once you finish the problem, you must provide a result with the following JSON structure:

{example_output}

Return this JSON for all the intents, not only the winner.

A score of 1 (the maximum) in an intent means that you are 100% sure that that is the correct intent.
Below 0.5 means that you have reasons to believe that that intent is not the appropriate.

The following JSON contains all the intent definitions:

{self.__intents_dict}

The following JSON contains all the entity definitions:

{self.__entities_dict}

Given all the previous instructions and training data, run the intent classification and named entity
recognition processes on this sentence: 

'{message}'

Only write the JSON answer. Do not write other things. Use double quotes to enclose the property names.
The output format is JSON, not List.
"""
        return prompt

    def train(self) -> None:
        self.__intents_dict = {}
        self.__entities_dict = {}
        for intent in self._state.intents:
            self.__intents_dict[intent.name] = intent.to_json()
            if not self._state.ic_config.use_intent_descriptions:
                del self.__intents_dict[intent.name]['description']
            if not self._state.ic_config.use_training_sentences:
                del self.__intents_dict[intent.name]['training_sentences']
            for parameter in intent.parameters:
                if parameter.entity.name not in self.__entities_dict:
                    self.__entities_dict[parameter.entity.name] = parameter.entity.to_json()
                    if not self._state.ic_config.use_entity_descriptions:
                        del self.__entities_dict[parameter.entity.name]['description']
                    if not self._state.ic_config.use_entity_synonyms:
                        for entry in self.__entities_dict[parameter.entity.name]['entries']:
                            del entry['synonyms']

    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        try:
            prompt = self._generate_prompt(message)
            if self._state.ic_config.llm_suite == LLMIntentClassifierConfiguration.OPENAI_LLM_SUITE:
                answer = self.predict_openai(prompt)
            elif self._state.ic_config.llm_suite == LLMIntentClassifierConfiguration.HUGGINGFACE_LLM_SUITE:
                answer = self.predict_huggingface(prompt)
            elif self._state.ic_config.llm_suite == LLMIntentClassifierConfiguration.HUGGINGFACE_INFERENCE_API_LLM_SUITE:
                answer = self.predict_huggingface_inference_api(prompt)
            elif self._state.ic_config.llm_suite == LLMIntentClassifierConfiguration.REPLICATE_LLM_SUITE:
                answer = self.predict_replicate(prompt)
            else:
                return []
        except Exception as _:
            logging.error(f"An error occurred while predicting the intent in state '{self._state.name}' with LLM "
                          f"Intent Classifier '{self._state.ic_config.llm_suite}'. See the attached exception:")
            traceback.print_exc()
            return []
        intent_classifier_results: list[IntentClassifierPrediction] = []
        for intent_name, prediction in answer.items():
            for intent in self._state.intents:
                if intent.name == intent_name:
                    matched_parameters: list[MatchedParameter] = []
                    if 'parameters' in prediction:
                        for parameter in intent.parameters:
                            if parameter.name in prediction['parameters']:
                                matched_parameters.append(MatchedParameter(parameter.name, prediction['parameters'][parameter.name], {}))
                            else:
                                matched_parameters.append(MatchedParameter(parameter.name, None, {}))
                    intent_classifier_results.append(IntentClassifierPrediction(
                        intent,
                        prediction['score'] if 'score' in prediction else 0,
                        message,
                        matched_parameters
                    ))
                    break
        return intent_classifier_results

    def predict_openai(self, prompt: str) -> dict[str, dict]:
        """Send the prompt to the OpenAI LLM.

        Args:
            prompt (str): the input prompt

        Returns:
            dict[str, dict]: the intent predictions
        """
        api_key = self._nlp_engine.get_property(nlp.OPENAI_API_KEY)
        model_name = self._nlp_engine.get_property(nlp.NLP_INTENT_OPENAI_MODEL_NAME)
        client = OpenAI(api_key=api_key)
        parameters = self._state.ic_config.parameters.copy()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            **parameters
        )
        return json.loads(response.choices[0].message.content)

    def predict_huggingface(self, prompt: str) -> dict[str, dict]:
        """Send the prompt to the HuggingFace (local) LLM.

        Args:
            prompt (str): the input prompt

        Returns:
            dict[str, dict]: the intent predictions
        """
        model_name = self._nlp_engine.get_property(nlp.NLP_INTENT_HF_MODEL_NAME)
        pipe = pipeline("text-generation", model=model_name)
        outputs = pipe(prompt)
        answer = outputs[0]['generated_text']
        return find_json(answer)

    def predict_huggingface_inference_api(self, prompt: str) -> dict[str, dict]:
        """Send the prompt to the HuggingFace Inference API LLM.

        Args:
            prompt (str): the input prompt

        Returns:
            dict[str, dict]: the intent predictions
        """
        api_key = self._nlp_engine.get_property(nlp.HF_API_KEY)
        model_name = self._nlp_engine.get_property(nlp.NLP_INTENT_HF_MODEL_NAME)
        headers = {"Authorization": f"Bearer {api_key}"}
        api_url = F"https://api-inference.huggingface.co/models/{model_name}"
        parameters = self._state.ic_config.parameters.copy()
        payload = {"inputs": prompt, "parameters": parameters}
        response = requests.post(api_url, headers=headers, json=payload)
        answer = response.json()[0]['generated_text']
        return find_json(answer)

    def predict_replicate(self, prompt: str) -> dict[str, dict]:
        """Send the prompt to the Replicate LLM.

        Args:
            prompt (str): the input prompt

        Returns:
            dict[str, dict]: the intent predictions
        """
        if 'REPLICATE_API_TOKEN' not in os.environ:
            os.environ['REPLICATE_API_TOKEN'] = self._nlp_engine.get_property(nlp.REPLICATE_API_KEY)
        parameters = self._state.ic_config.parameters.copy()
        parameters['prompt'] = prompt
        answer = replicate.run(
            self._nlp_engine.get_property(nlp.NLP_INTENT_REPLICATE_MODEL_NAME),
            input=parameters,
        )
        answer = ''.join(answer)
        return find_json(answer)
