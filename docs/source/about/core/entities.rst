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

Base entities
-------------

In Bot-Framework, we include a set of predefined entities that can be used in any intent parameter like custom entities.
The difference is that you don't need to define them. We do it for you!

The following list describes all currently implemented base entities:

.. csv-table::
    :file: base_entities.csv
    :header-rows: 1

