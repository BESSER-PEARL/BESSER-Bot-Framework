Intent classification
=====================

When a user sends a message to the bot, it needs to recognize its intention among a set of :doc:`intents <../core/intents>`.
In NLP, this problem is known as Text Classification.

    Given an user message, the bot must classify it into one of the possible intents.

To successfully do this, it is necessary to provide a set of example sentences for each intent
(this is the training data).

In this section, we delve into the different intent classifiers available in BBF. Each one has its pros and cons.

Each bot state has its own intent classifier. This is because each intent classifier is trained to recognize only those
intents allowed in its state. This way, you can choose the intent classifier that better suits for each state depending
on the needs. Let's see how to configure this.

.. _intent-classifier-configuration:

Configuration
-------------

Each state has an :doc:`intent classifier configuration <../../api/nlp/intent_classifier_configuration>`.
that defines its intent classifier's properties. We provide :doc:`default intent classifier configurations <../../api/library/intent_classifier_configuration_library>`
that can be imported and used:

.. code:: python

    from besser.bot.library.intent.intent_classifier_configuration_library import openai_config


We can set a default configuration for all states (note that this would replace any previously defined configuration):

.. code:: python

    bot = Bot('example_bot')
    bot.set_default_ic_config(openai_config)

This is how you can create an intent classifier configuration:

.. code:: python

    from besser.bot.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration

    openai_config = LLMIntentClassifierConfiguration(
        llm_suite=LLMIntentClassifierConfiguration.OPENAI_LLM_SUITE,
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

You can set a configuration for a specific state:

.. code:: python

    example_state = bot.new_state('example_state', ic_config=openai_config)

.. note::

    If you don't specify any configuration for a state, the :any:`simple-intent-classifier` will be selected by default.

.. note::

    All intent classifier configuration classes implement the :class:`~besser.bot.nlp.intent_classifier.intent_classifier_configuration.IntentClassifierConfiguration` class
    and all intent classifiers implement the :class:`~besser.bot.nlp.intent_classifier.intent_classifier.IntentClassifier` class


.. _simple-intent-classifier:

Simple Intent Classifier
------------------------

The :class:`~besser.bot.nlp.intent_classifier.simple_intent_classifier.SimpleIntentClassifier` is based on a basic
`Keras <https://keras.io/>`_ neural network as the prediction model. It is trained with the intent's training sentences.
When running, it is able to predict the intent of a message if it is close to any of the training sentences.

You can see all the configuration possibilities of this intent classifier here:
:class:`~besser.bot.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`

The :obj:`~besser.bot.nlp.NLP_PRE_PROCESSING` bot property influences the performance of this intent classifier. If you
decide to preprocess the user messages (this is done before the intent prediction), the intent predictions will
probably be more accurate.

When to use it?
~~~~~~~~~~~~~~~

- If you want a very light, customizable and quickly trainable intent classifier.
- If you are certain of how the user messages will look like.
- If you want to restrict the user's writing freedom, forcing him/her to write in a particular way or to choose from a
  predefined set of messages (with buttons).

Pros
~~~~

- Free
- Fast training
- Fast predictions
- Very small

Cons
~~~~

- You need to provide training sentences (quantity and quality increases the success probabilities)
- Not possible to understand semantic similarities, only word similarities. For example, if a training sentence is 'yes'
  and the user says 'of course' (something not present in the training sentences), the prediction will fail.
- If 2 or more intents have very similar training sentences, probabilities of wrong predictions increase

Example scenario
~~~~~~~~~~~~~~~~

Imagine your bot has a state where it asks some question to the user, expecting a yes/no answer:

.. code:: python

    yes_intent = bot.new_intent('yes_intent', ['Yes'])

    no_intent = bot.new_intent('no_intent', ['No'])

    example_state = bot.new_state('example_state', ic_config=SimpleIntentClassifierConfiguration())

    def example_body(session: Session):
        websocket_platform.reply(session, 'Do you want to continue talking?')
        websocket_platform.reply_options(session, ['Yes', 'No'])

    example_state.set_body(example_body)
    example_state.when_intent_matched_go_to(yes_intent, state1)
    example_state.when_intent_matched_go_to(no_intent, state2)

In this kind of situations, the Simple Intent Classifier will satisfy the bot needs. You can also remove the
reply_options message and let the user write, although if you want to force the user reply, this is strongly recommended.


.. _llm-intent-classifier:

LLM Intent Classifier
---------------------

The :class:`~besser.bot.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier` uses a Large Language Model
(LLM) to predict the intent of a message. LLMs are multimodal models that can solve a wide variety of tasks just by
providing them the right prompts in natural language. In this case, we can ask them to classify a sentence into the
appropriate intent.

You can see all the configuration possibilities of this intent classifier here:
:class:`~besser.bot.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`

When to use it?
~~~~~~~~~~~~~~~

- If you want a powerful and very smart intent classifier.
- If you don't quite know how the user messages will look like.
- If you want to give the users writing freedom.

Pros
~~~~

- No need to train it. It is a general purpose model.
- Through API, no need to host it (also possible to run it locally with HuggingFace)
- No need for training sentences, just intent descriptions (you can also use both).
- Understands semantic similarities. For example, if a training sentence is 'yes' and the user says 'of course'
  (something not present in the training sentences), the prediction will probably hit.
- You can select any LLM you want (even different LLMs for each state)
- Powerful Named Entity Recognition integrated.

Cons
~~~~

- APIs not free to use
- LLMs are big (this can only affect you if you run them locally)
- Some predictions may be slow (a few seconds)

Example scenario
~~~~~~~~~~~~~~~~

Imagine your bot has a state where some of the possible intents is a 'help' intent, intended to guide the
user on how to use the bot. Since there are a lot of different ways the user could ask for help, and we don't
want to think about them all, we can simply provide an intent description and use the LLM Intent Classifier:

.. code:: python

    from besser.bot.library.intent.intent_classifier_configuration_library import openai_config

    help_intent = bot.new_intent(
        name='help_intent',
        description='The user needs help to be able to use the chatbot properly or to find some information'
    )

    example_state = bot.new_state('example_state', ic_config=openai_config)

    def example_body(session: Session):
        # ...

    example_state.set_body(example_body)
    example_state.when_intent_matched_go_to(intent1, state1)
    # ...
    example_state.when_intent_matched_go_to(help_intent, help_state)

Available LLM suites
~~~~~~~~~~~~~~~~~~~~

- `OpenAI <https://openai.com>`_: The OpenAI API gives access to the latest GPT models.
   - Recommended LLMs:
      - gpt-4
      - gpt-4-turbo-preview
      - gpt-3.5-turbo
   - Necessary bot properties:
      - :obj:`~besser.bot.nlp.OPENAI_API_KEY`
      - :obj:`~besser.bot.nlp.NLP_INTENT_OPENAI_MODEL_NAME`
- `HuggingFace <https://huggingface.co/>`_: There are plenty of free open-source LLMs available in HuggingFace you can run in your machine.
   - Recommended LLMs:
      - mistralai/Mixtral-8x7B-v0.1 (big LLM)
      - mistralai/Mistral-7B-v0.1 (small LLM)
      - meta-llama/Llama-2-70b-chat (big LLM)
      - meta-llama/Llama-2-7b-chat (small LLM)
   - Necessary bot properties:
      - :obj:`~besser.bot.nlp.NLP_INTENT_HF_MODEL_NAME`
- `HuggingFace Inference API <https://huggingface.co/docs/api-inference>`_: HuggingFace's LLMs can be used through its API instead of locally.
   - Same models as in HuggingFace
   - Necessary bot properties:
      - :obj:`~besser.bot.nlp.HF_API_KEY`
      - :obj:`~besser.bot.nlp.NLP_INTENT_HF_MODEL_NAME`
- `Replicate <https://replicate.com/>`_: A platform that hosts a wide variety of LLMs that can be used through its API.
   - Recommended LLMs:
      - mistralai/mixtral-8x7b-instruct-v0.1 (big LLM)
      - mistralai/mistral-7b-instruct-v0.2 (small LLM)
      - meta/llama-2-70b-chat (big LLM)
      - meta/llama-2-7b-chat (small LLM)
   - Necessary bot properties:
      - :obj:`~besser.bot.nlp.REPLICATE_API_KEY`
      - :obj:`~besser.bot.nlp.NLP_INTENT_REPLICATE_MODEL_NAME`

(The models suggested were tested on 2024-02-15)

API References
--------------

- Bot: :class:`besser.bot.core.bot.Bot`
- Bot.new_intent(): :meth:`besser.bot.core.bot.Bot.new_intent`
- Bot.new_state(): :meth:`besser.bot.core.bot.Bot.new_state`
- Bot.set_default_ic_config(): :meth:`besser.bot.core.bot.Bot.set_default_ic_config`
- Intent: :class:`besser.bot.core.intent.intent.Intent`
- IntentClassifierConfiguration: :class:`besser.bot.nlp.intent_classifier.intent_classifier_configuration.IntentClassifierConfiguration`
- LLMIntentClassifierConfiguration: :class:`besser.bot.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`
- openai_config: :obj:`besser.bot.library.intent.intent_classifier_configuration_library.openai_config`
- Session: :class:`besser.bot.core.session.Session`
- SimpleIntentClassifierConfiguration: :class:`besser.bot.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`
- State: :class:`besser.bot.core.state.State`
- State.set_body(): :meth:`besser.bot.core.state.State.set_body`
- State.when_intent_matched_go_to(): :meth:`besser.bot.core.state.State.when_intent_matched_go_to`



