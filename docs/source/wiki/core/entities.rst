Entities
========

Entities are used to specify the type of information to extract from user inputs. These entities are embedded in
intent parameters.

Custom entities
---------------

Let's see how to create your own entities for your bot.

.. code:: python

    bot = Bot('weather_bot')
    ...
    city_entity = bot.new_entity('city_entity', entries={
        'Barcelona': ['BCN', 'barna'],
        'Luxembourg': ['LUX'],
    })

Entities have a set of **entries**. Each entity entry is composed by a **value** (e.g. 'Barcelona') and a list of
(optional) **synonyms** of the value (useful for values that can be called in different ways, but refer to the same
concept). In this example entity, you could add all the cities you want the bot to be able to recognise. In a real use
case, you could also get a complete list of cities in a country and create an entity with that entries.

In :any:`intents-with-parameters`, we explain how to embed entities in intent parameters.

Entity descriptions
-------------------

If you want to use the :any:`llm-intent-classifier`, you can create an entity without values. Instead, you
just would need to provide a description for that entity, although you can still add values to it. This is
an example intent with a description:

.. code:: python

    email_entity = bot.new_entity(
        name='email_entity',
        description='An entity containing email addresses',
    )

In this example, the LLM Intent Classifier will be able to recognize and extract email addresses from user messages.

.. _base-entities:

Base entities
-------------

In Bot-Framework, we include a set of predefined entities that can be used in any intent parameter like custom entities.
The difference is that you don't need to define them. We do it for you!

The following list describes all currently implemented base entities:

.. csv-table::
    :file: base_entities.csv
    :header-rows: 1

Let's see how to use base entities with an example:

.. code:: python

    from besser.bot.library.entity.base_entities import number_entity
    ...
    bot.add_entity(number_entity)

    age_intent = bot.new_intent('age_intent', [
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

- Bot: :class:`besser.bot.core.bot.Bot`
- Bot.add_entity(): :meth:`besser.bot.core.bot.Bot.add_entity`
- Bot.new_entity(): :meth:`besser.bot.core.bot.Bot.new_entity`
- Entity: :class:`besser.bot.core.entity.entity.Entity`
- EntityEntry: :class:`besser.bot.core.entity.entity_entry.EntityEntry`
- Intent: :class:`besser.bot.core.intent.intent.Intent`
- Intent.parameter(): :meth:`besser.bot.core.intent.intent.Intent.parameter`
- IntentClassifierPrediction: :class:`besser.bot.nlp.intent_classifier.intent_classifier_prediction.IntentClassifierPrediction`
- MatchedParameter: :class:`besser.bot.nlp.ner.matched_parameter.MatchedParameter`
- Session: :class:`besser.bot.core.session.Session`
- Session.reply(): :meth:`besser.bot.core.session.Session.reply`
- Session.set(): :meth:`besser.bot.core.session.Session.set`

