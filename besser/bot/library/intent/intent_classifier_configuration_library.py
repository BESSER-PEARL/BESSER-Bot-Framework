from besser.bot.nlp import llm
from besser.bot.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration

openai_config = LLMIntentClassifierConfiguration(
    llm_suite=llm.OPENAI_LLM_SUITE,
    parameters={
        "seed": None,
        "top_p": 1,
        "temperature": 1,
    },
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False
)
"""
Default configuration for LLM Intent Classifiers powered by `OpenAI <https://openai.com>`_
Parameters documentation: https://platform.openai.com/docs/api-reference/chat/create
"""

hf_config = LLMIntentClassifierConfiguration(
    llm_suite=llm.HUGGINGFACE_LLM_SUITE,
    parameters={},
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False
)
"""
Default configuration for LLM Intent Classifiers powered by `HuggingFace <https://huggingface.co/models>`_
Parameters documentation: https://huggingface.co/docs/transformers/main_classes/pipelines#transformers.TextGenerationPipeline
"""

hf_api_config = LLMIntentClassifierConfiguration(
    llm_suite=llm.HUGGINGFACE_INFERENCE_API_LLM_SUITE,
    parameters={
        "top_k": None,
        "top_p": None,
        "temperature": 1,
        "repetition_penalty": None,
        "max_new_tokens": None,
        "max_time": None,
        "return_full_text": False,
        "num_return_sequences": 1,
        "do_sample": True,
        "options": {
            "use_cache": True,
            "wait_for_model": False
        }
    },
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False
)
"""
Default configuration for LLM Intent Classifiers powered by `HuggingFace Inference API <https://huggingface.co/docs/api-inference>`_
Parameters documentation: https://huggingface.co/docs/api-inference/detailed_parameters#text-generation-task
"""

replicate_config = LLMIntentClassifierConfiguration(
    llm_suite=llm.REPLICATE_LLM_SUITE,
    parameters={
        # TODO: Find parameters docs
        "debug": False,
        "system_prompt": "",
        "temperature": 0.75,
        "max_new_tokens": 500,
        "min_new_tokens": -1,
        "top_k": 50,
        "top_p": 0.9,
        "seed": 123
    },
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False
)
"""
Default configuration for LLM Intent Classifiers powered by `Replicate <https://replicate.com>`_
Parameters documentation (check this LLM as an example): https://replicate.com/meta/llama-2-70b-chat
"""