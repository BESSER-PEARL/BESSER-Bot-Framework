Intents
=======

Intents define the *intentions* or *goals* the user can express to a bot. In this article we review how to create
intents with the Bot Framework.

Simple intents
--------------

First of all, we need to create a bot and some states:

.. code:: python

    bot = Bot('example_bot')
    ...
    initial_state = bot.new_state('initial_state')
    handle_hello_state = bot.new_state('handle_hello_state')

Let's say we want to say hello to the bot. For that, we need an intent that defines how do "hello" messages look like.
To do that, we create an intent writing some **training sentences** as example messages we expect the bot to understand
in a "hello" message:

.. code:: python

    hello_intent = bot.new_intent('hello_intent', [
        'hello',
        'hi'
    ])

Once we have defined our intent, we need to add the proper :doc:`transitions <transitions>` to explicitly define where
this intent is expected to be received and where is the user expected to move once the intent is received:

.. code:: python

    initial_state.when_intent_matched_go_to(hello_intent, handle_hello_state)

When the user is in initial_state, the bot is waiting for a user message. Once the user sends a message, the bot will
classify it into one of the possible incoming intents in initial_state (here, only hello_intent can be recognized). If
the message's intent is hello_intent, the user will move to handle_hello_state, as we have defined it.

.. figure:: ../../img/intents_diagram.png
   :alt: Intent diagram

   The bot we just created, has 2 states linked by an intent.

.. _intents-with-parameters:

Intents with parameters
-----------------------

Intents can have embedded parameters. This means that we can extract data from a user message. At the same time, this
can help reducing the number of intents in a bot.

We are going to create an intent to ask about the weather in a city.

.. code:: python

    weather_intent = bot.new_intent('weather_intent', [
        'what is the weather in CITY?',
        'tell me the weather in CITY',
        'weather in CITY'
    ])

As you can guess, the *CITY* fragment of the training sentences is going to host a parameter where the user can say any
city. Defining the intent parameter is really simple:

.. code:: python

    weather_intent.parameter('city1', 'CITY', city_entity)

Intent parameters have a **name**, a **fragment** that indicates the position of the parameter in the intent's training
sentences and an **entity** that defines the values that can be matched in the parameter.

See the :doc:`entities <entities>` guide to learn about them.

.. note::

    You can also add a list of parameters directly in the intent creation:

    .. code:: python

        weather_intent = bot.new_intent('weather_intent', training_sentences, parameters)

Now let's see how the bot can access the intent parameters in runtime. Let's say we add the following transition to
another state:

.. code:: python

    initial_state.when_intent_matched_go_to(weather_intent, handle_weather_state)

The access to the intent parameters is done within the body of the state where the user moves after writing the weather
message. So let's define the body of handle_weather_state:

.. code:: python

    def handle_weather_body(session: Session):
        predicted_intent = session.predicted_intent
        city = predicted_intent.get_parameter('city1')
        if city.value is None: # Sometimes the intent can be recognized, but not the parameters
            session.reply("Sorry, I didn't get the city")
        else:
            # Here we would call some API to get the temperature of the city
            temperature = some_service.get_temperature(city)
            session.reply(f"The weather in {city.value} is {temperature}°C")
            if temperature < 15:
                session.reply('🥶')
            else:
                session.reply('🥵')