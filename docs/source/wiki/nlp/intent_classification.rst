Intent classification
=====================

When a user sends a message to the agent, it needs to recognize its intention among a set of :doc:`intents <../core/intents>`.
In NLP, this problem is known as Text Classification.

    Given an user message, the agent must classify it into one of the possible intents.

To successfully do this, it is necessary to provide a set of example sentences for each intent
(this is the training data).

In this section, we delve into the different intent classifiers available in BBF. Each one has its pros and cons.

Each agent state has its own intent classifier. This is because each intent classifier is trained to recognize only those
intents allowed in its state. This way, you can choose the intent classifier that better suits for each state depending
on the needs. Let's see how to configure this.

.. _intent-classifier-configuration:

Configuration
-------------

Each state has an :doc:`intent classifier configuration <../../api/nlp/intent_classifier_configuration>`.
that defines its intent classifier's properties.

This is how you can create an intent classifier configuration:

.. code:: python

    from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration

    agent = Agent('example_agent')

    simple_config = SimpleIntentClassifierConfiguration(
        activation_last_layer='sigmoid',
        activation_hidden_layers='tanh',
        lr=0.001
    )

We can set a configuration for a specific state:

.. code:: python

    example_state = agent.new_state('example_state', ic_config=simple_config)

Or a default configuration for all states (note that this would replace any previously defined configuration):

.. code:: python

    agent.set_default_ic_config(simple_config)

.. note::

    If you don't specify any configuration for a state, the :any:`simple-intent-classifier` will be selected by default.

.. note::

    All intent classifier configuration classes implement the :class:`~besser.agent.nlp.intent_classifier.intent_classifier_configuration.IntentClassifierConfiguration` class
    and all intent classifiers implement the :class:`~besser.agent.nlp.intent_classifier.intent_classifier.IntentClassifier` class


.. _simple-intent-classifier:

Simple Intent Classifier
------------------------

The :class:`~besser.agent.nlp.intent_classifier.simple_intent_classifier.SimpleIntentClassifier` is based on a basic
`Keras <https://keras.io/>`_ neural network as the prediction model. It is trained with the intent's training sentences.
When running, it is able to predict the intent of a message if it is close to any of the training sentences.

You can see all the configuration possibilities of this intent classifier here:
:class:`~besser.agent.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`

The :obj:`~besser.agent.nlp.NLP_PRE_PROCESSING` agent property influences the performance of this intent classifier. If you
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

Imagine your agent has a state where it asks some question to the user, expecting a yes/no answer:

.. code:: python

    yes_intent = agent.new_intent('yes_intent', ['Yes'])

    no_intent = agent.new_intent('no_intent', ['No'])

    example_state = agent.new_state('example_state', ic_config=SimpleIntentClassifierConfiguration())

    def example_body(session: Session):
        websocket_platform.reply(session, 'Do you want to continue talking?')
        websocket_platform.reply_options(session, ['Yes', 'No'])

    example_state.set_body(example_body)
    example_state.when_intent_matched_go_to(yes_intent, state1)
    example_state.when_intent_matched_go_to(no_intent, state2)

In this kind of situations, the Simple Intent Classifier will satisfy the agent needs. You can also remove the
reply_options message and let the user write, although if you want to force the user reply, this is strongly recommended.


.. _llm-intent-classifier:

LLM Intent Classifier
---------------------

The :class:`~besser.agent.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier` uses a :doc:`Large Language Model
(LLM) <llm>` to predict the intent of a message. LLMs are multimodal models that can solve a wide variety of tasks just by
providing them the right prompts in natural language. In this case, we can ask them to classify a sentence into the
appropriate intent.

You can see all the configuration possibilities of this intent classifier here:
:class:`~besser.agent.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`

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

Imagine your agent has a state where some of the possible intents is a 'help' intent, intended to guide the
user on how to use the agent. Since there are a lot of different ways the user could ask for help, and we don't
want to think about them all, we can simply provide an intent description and use the LLM Intent Classifier:

.. code:: python

    from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
    from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI

    agent = Agent('example_agent')
    llm = LLMOpenAI(agent=agent, name='gpt-4o-mini')

    ic_config = LLMIntentClassifierConfiguration(
        llm_name='gpt-4o-mini',
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

    help_intent = agent.new_intent(
        name='help_intent',
        description='The user needs help to be able to use the agent properly or to find some information'
    )

    example_state = agent.new_state('example_state', ic_config=ic_config)

    def example_body(session: Session):
        # ...

    example_state.set_body(example_body)
    example_state.when_intent_matched_go_to(intent1, state1)
    # ...
    example_state.when_intent_matched_go_to(help_intent, help_state)

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.new_intent(): :meth:`besser.agent.core.agent.Agent.new_intent`
- Agent.new_state(): :meth:`besser.agent.core.agent.Agent.new_state`
- Agent.set_default_ic_config(): :meth:`besser.agent.core.agent.Agent.set_default_ic_config`
- Intent: :class:`besser.agent.core.intent.intent.Intent`
- IntentClassifierConfiguration: :class:`besser.agent.nlp.intent_classifier.intent_classifier_configuration.IntentClassifierConfiguration`
- LLMIntentClassifierConfiguration: :class:`besser.agent.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`
- LLMOpenAI: :class:`besser.agent.nlp.llm.llm_openai_api.LLMIntentClassifierConfiguration`
- Session: :class:`besser.agent.core.session.Session`
- SimpleIntentClassifierConfiguration: :class:`besser.agent.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`
- State: :class:`besser.agent.core.state.State`
- State.set_body(): :meth:`besser.agent.core.state.State.set_body`
- State.when_intent_matched_go_to(): :meth:`besser.agent.core.state.State.when_intent_matched_go_to`
