Entities
========

Entities are used to specify the type of information to extract from user inputs. These entities are embedded in
intent parameters.

Custom entities
---------------

Let's see how to create your own entities for your agent.

.. code:: python

    agent = Agent('weather_agent')
    ...
    city_entity = agent.new_entity('city_entity', entries={
        'Barcelona': ['BCN', 'barna'],
        'Luxembourg': ['LUX'],
    })

Entities have a set of **entries**. Each entity entry is composed by a **value** (e.g. 'Barcelona') and a list of
(optional) **synonyms** of the value (useful for values that can be called in different ways, but refer to the same
concept). In this example entity, you could add all the cities you want the agent to be able to recognise. In a real use
case, you could also get a complete list of cities in a country and create an entity with that entries.

In :any:`intents-with-parameters`, we explain how to embed entities in intent parameters.

Entity descriptions
-------------------

If you want to use the :any:`llm-intent-classifier`, you can create an entity without values. Instead, you
just would need to provide a description for that entity, although you can still add values to it. This is
an example intent with a description:

.. code:: python

    email_entity = agent.new_entity(
        name='email_entity',
        description='An entity containing email addresses',
    )

In this example, the LLM Intent Classifier will be able to recognize and extract email addresses from user messages.

.. _base-entities:

Base entities
-------------

In BESSER Agentic Framework, we include a set of predefined entities that can be used in any intent parameter like custom entities.
The difference is that you don't need to define them. We do it for you!

The following list describes all currently implemented base entities:

.. csv-table::
    :file: base_entities.csv
    :header-rows: 1

Let's see how to use base entities with an example:

.. code:: python

    from besser.agent.library.entity.base_entities import number_entity
    ...
    agent.add_entity(number_entity)

    age_intent = agent.new_intent('age_intent', [
        'I am NUM years old',
        'My age is NUM
    ])
    age_intent.parameter('age', 'NUM', number_entity)
    ...
    def age_body(session: Session):
        predicted_intent: IntentClassifierPrediction = session.predicted_intent
        age = predicted_intent.get_parameter('age').value
        session.set('age', age) # Save the age in the user session
        session.reply('Thanks for the information')
    ...

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.add_entity(): :meth:`besser.agent.core.agent.Agent.add_entity`
- Agent.new_entity(): :meth:`besser.agent.core.agent.Agent.new_entity`
- Entity: :class:`besser.agent.core.entity.entity.Entity`
- EntityEntry: :class:`besser.agent.core.entity.entity_entry.EntityEntry`
- Intent: :class:`besser.agent.core.intent.intent.Intent`
- Intent.parameter(): :meth:`besser.agent.core.intent.intent.Intent.parameter`
- IntentClassifierPrediction: :class:`besser.agent.nlp.intent_classifier.intent_classifier_prediction.IntentClassifierPrediction`
- MatchedParameter: :class:`besser.agent.nlp.ner.matched_parameter.MatchedParameter`
- Session: :class:`besser.agent.core.session.Session`
- Session.reply(): :meth:`besser.agent.core.session.Session.reply`
- Session.set(): :meth:`besser.agent.core.session.Session.set`

