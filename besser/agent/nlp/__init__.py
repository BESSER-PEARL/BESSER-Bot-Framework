"""Definition of the agent properties within the ``nlp`` (Natural Language Processing) section"""

from besser.agent.core.property import Property

SECTION_NLP = 'nlp'

NLP_LANGUAGE = Property(SECTION_NLP, 'nlp.language', str, 'en')
"""
The agenr language. This is the expected language the users will talk to the agent. Using another language may 
affect the quality of some NLP processes.

The list of available languages can be found at `snowballstemmer <https://pypi.org/project/snowballstemmer/>`_.
Note that luxembourgish (lb) is also partially supported, as the language can be chosen, yet the stemmer is still a work in progress.

Languages must be written in `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ format (e.g., 'en'
for English)

name: ``nlp.language``

type: ``str``

default value: ``en``
"""

NLP_REGION = Property(SECTION_NLP, 'nlp.region', str, 'US')
"""
The language region. If specified, it can improve some NLP process You can find a list of regions 
`here <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

name: ``nlp.region``

type: ``str``

default value: ``US``
"""

NLP_TIMEZONE = Property(SECTION_NLP, 'nlp.timezone', str, 'Europe/Madrid')
"""
The timezone. It is used for datetime-related tasks, e.g., to get the current datetime. A list of timezones can be found
`here. <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_

name: ``nlp.timezone``

type: ``str``

default value: ``Europe/Madrid``
"""

NLP_PRE_PROCESSING = Property(SECTION_NLP, 'nlp.pre_processing', bool, True)
"""
Whether to use text pre-processing or not. `Stemming <https://en.wikipedia.org/wiki/Stemming>`_ is the process of reducing
inflected (or sometimes derived) words to their word stem, base or root form.

Currently, only :class:`~besser.agent.nlp.intent_classifier.simple_intent_classifier.SimpleIntentClassifier` and
:class:`~besser.agent.nlp.ner.simple_ner.SimpleNER` use this property. If
:class:`~besser.agent.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier` is used, this property is ignored.

For example 'games' and 'gaming' are stemmed to 'game'.

It can improve the NLP process by generalizing user inputs.

name: ``nlp.pre_processing``

type: ``bool``

default value: ``True``
"""

NLP_INTENT_THRESHOLD = Property(SECTION_NLP, 'nlp.intent_threshold', float, 0.4)
"""
The threshold for the Intent Classification problem. If none of its predictions have a score greater than the threshold,
it will be considered that no intent was detected with enough confidence (and therefore, moving to a fallback scenario).

name: ``nlp.intent_threshold``

type: ``float``

default value: ``0.4``
"""

NLP_STT_HF_MODEL = Property(SECTION_NLP, 'nlp.speech2text.hf.model', str, None)
"""
The name of the Hugging Face model for the HFSpeech2Text agent component. If none is provided, the component will not be 
activated.

name: ``nlp.speech2text.hf.model``

type: ``str``

default value: ``None``
"""

NLP_STT_SR_ENGINE = Property(SECTION_NLP, 'nlp.speech2text.sr.engine', str, None)
"""
The name of the transcription engine for the Speech Recognition agent component. If none is provided, the component will
not be activated.

name: ``nlp.speech2text.sr.engine``

type: ``str``

default value: ``None``
"""

OPENAI_API_KEY = Property(SECTION_NLP, 'nlp.openai.api_key', str, None)
"""
The OpenAI API key, necessary to use an OpenAI LLM.

name: ``nlp.openai.api_key``

type: ``str``

default value: ``None``
"""

HF_API_KEY = Property(SECTION_NLP, 'nlp.hf.api_key', str, None)
"""
The HuggingFace (Inference) API key, necessary to use a HuggingFace Inference API LLM.

name: ``nlp.hf.api_key``

type: ``str``

default value: ``None``
"""

REPLICATE_API_KEY = Property(SECTION_NLP, 'nlp.replicate.api_key', str, None)
"""
The Replicate API key, necessary to use a Replicate LLM.

name: ``nlp.replicate.api_key``

type: ``str``

default value: ``None``
"""
