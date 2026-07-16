"""Definition of the agent properties within the ``nlp`` (Natural Language Processing) section"""

from baf.core.property import Property

NLP_LANGUAGE = Property('nlp.language', str, 'en')
"""
The agent language. This is the expected language the users will talk to the agent. Using another language may 
affect the quality of some NLP processes.

The list of available languages can be found at `snowballstemmer <https://pypi.org/project/snowballstemmer/>`_.
Note that luxembourgish (lb) is also partially supported, as the language can be chosen, yet the stemmer is still a work in progress.

Languages must be written in `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ format (e.g., 'en'
for English)

name: ``nlp.language``

type: ``str``

default value: ``en``
"""

NLP_REGION = Property('nlp.region', str, 'US')
"""
The language region. If specified, it can improve some NLP process You can find a list of regions 
`here <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

name: ``nlp.region``

type: ``str``

default value: ``US``
"""

NLP_TIMEZONE = Property('nlp.timezone', str, 'Europe/Madrid')
"""
The timezone. It is used for datetime-related tasks, e.g., to get the current datetime. A list of timezones can be found
`here. <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_

name: ``nlp.timezone``

type: ``str``

default value: ``Europe/Madrid``
"""

NLP_PRE_PROCESSING = Property('nlp.pre_processing', bool, True)
"""
Whether to use text pre-processing or not. `Stemming <https://en.wikipedia.org/wiki/Stemming>`_ is the process of reducing
inflected (or sometimes derived) words to their word stem, base or root form.

Currently, only :class:`~baf.nlp.intent_classifier.simple_intent_classifier_pytorch.SimpleIntentClassifierTorch`,
:class:`~baf.nlp.intent_classifier.simple_intent_classifier_tensorflow.SimpleIntentClassifierTF` and
:class:`~baf.nlp.ner.simple_ner.SimpleNER` use this property. If
:class:`~baf.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier` is used, this property is ignored.

For example 'games' and 'gaming' are stemmed to 'game'.

It can improve the NLP process by generalizing user inputs.

name: ``nlp.pre_processing``

type: ``bool``

default value: ``True``
"""

NLP_INTENT_THRESHOLD = Property('nlp.intent_threshold', float, 0.4)
"""
The threshold for the Intent Classification problem. If none of its predictions have a score greater than the threshold,
it will be considered that no intent was detected with enough confidence (and therefore, moving to a fallback scenario).

name: ``nlp.intent_threshold``

type: ``float``

default value: ``0.4``
"""


OPENAI_API_KEY = Property('nlp.openai.api_key', str, None)
"""
The OpenAI API key, necessary to use an OpenAI LLM.

name: ``nlp.openai.api_key``

type: ``str``

default value: ``None``
"""

HF_TOKEN = Property('nlp.huggingface.token', str, None)
"""
The HuggingFace (Inference) API key, necessary to use a HuggingFace Inference API LLM.

name: ``nlp.huggingface.token``

type: ``str``

default value: ``None``
"""

REPLICATE_API_KEY = Property('nlp.replicate.api_key', str, None)
"""
The Replicate API key, necessary to use a Replicate LLM.

name: ``nlp.replicate.api_key``

type: ``str``

default value: ``None``
"""

MISTRAL_API_KEY = Property('nlp.mistral.api_key', str, None)
"""
The Mistral AI API key, necessary to use a Mistral LLM.

name: ``nlp.mistral.api_key``

type: ``str``

default value: ``None``
"""

DEEPSEEK_API_KEY = Property('nlp.deepseek.api_key', str, None)
"""
The DeepSeek API key, necessary to use a DeepSeek LLM.

name: ``nlp.deepseek.api_key``

type: ``str``

default value: ``None``
"""

GOOGLE_API_KEY = Property('nlp.google.api_key', str, None)
"""
The Google AI (Gemini) API key, necessary to use a Google LLM.

name: ``nlp.google.api_key``

type: ``str``

default value: ``None``
"""

META_API_KEY = Property('nlp.meta.api_key', str, None)
"""
The Meta AI API key, necessary to use a Meta Llama LLM via Meta's hosted API.

name: ``nlp.meta.api_key``

type: ``str``

default value: ``None``
"""

ANTHROPIC_API_KEY = Property('nlp.anthropic.api_key', str, None)
"""
The Anthropic API key, necessary to use an Anthropic Claude LLM.

name: ``nlp.anthropic.api_key``

type: ``str``

default value: ``None``
"""

QWEN_API_KEY = Property('nlp.qwen.api_key', str, None)
"""
The Alibaba DashScope API key, necessary to use a Qwen LLM.

name: ``nlp.qwen.api_key``

type: ``str``

default value: ``None``
"""

XAI_API_KEY = Property('nlp.xai.api_key', str, None)
"""
The xAI API key, necessary to use an xAI Grok LLM.

name: ``nlp.xai.api_key``

type: ``str``

default value: ``None``
"""

GROQ_API_KEY = Property('nlp.groq.api_key', str, None)
"""
The Groq API key, necessary to use a Groq-hosted LLM.

name: ``nlp.groq.api_key``

type: ``str``

default value: ``None``
"""

TOGETHER_API_KEY = Property('nlp.together.api_key', str, None)
"""
The Together AI API key, necessary to use a Together AI-hosted LLM.

name: ``nlp.together.api_key``

type: ``str``

default value: ``None``
"""

OPENROUTER_API_KEY = Property('nlp.openrouter.api_key', str, None)
"""
The OpenRouter API key, necessary to use an OpenRouter-proxied LLM.

name: ``nlp.openrouter.api_key``

type: ``str``

default value: ``None``
"""
