Your first bot
==============

Welcome to *Your first bot* 🤖 tutorial! Here you will learn from the very basics of the framework how to create
chatbots with pure Python. Once you finish this 5 minutes guide, you will be ready to build your own chatbots.
Take advantage of our documentation to deepen into anything you need for your bots.

The greetings bot
-----------------

.. figure:: img/greetings_bot_diagram.png
   :alt: Greetings bot diagram

   Greetings bot diagram

The chatbot we are going to create has a really simple structure. The user is intended to greet the bot and answer a
simple *How are you?* question. This workflow is repeated *ad infinitum*.

You can also see the full bot code :doc:`here <examples/greetings_bot>`

Import the dependencies
--------------------------

Before starting coding the bot itself, we need to import the necessary dependencies.

.. code:: python

    from besser.bot.core.bot import Bot
    from besser.bot.core.session import Session

.. note::

    Optionally, you can set the logging system to display log messages at the INFO level or higher. By doing this, you will
    see all the bot actions through the terminal, which can help you understand the bot behaviour.

    .. code:: python

        import logging
        logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')


Create the bot
--------------

Let's start creating your bot. We only need to specify its name.

.. code:: python

    bot = Bot('greetings_bot')


.. note::

   Some bot components may need you to specify some properties. Some may be compulsory (e.g. an API key), others can
   be optional and others may have default values so you don't necessarily need to specify them.

   For this bot we don't need to set any property, but you can see the
   :doc:`configuration properties <about/configuration_properties>` to learn more.


Define the platform your chatbot will use.

.. code:: python

    websocket_platform = bot.use_websocket_platform(use_ui=True)

The bot platform will allow you to communicate with your chatbot using a bidirectional channel, so you can send and
receive messages.

See :doc:`Platforms <about/platforms>` to learn more.

States
------

Now, we are going to create the bot states you can see in the previous figure.

.. warning::

   Every bot has 1 (and only 1) initial state! See :doc:`States <about/core/states>` to learn more.

.. code:: python

    initial_state = bot.new_state('initial_state', initial=True)
    hello_state = bot.new_state('hello_state')
    good_state = bot.new_state('good_state')
    bad_state = bot.new_state('bad_state')

Intents
-------

The next step is to define all the intents for the bot. *Intent* refers to the specific purpose or goal that a user has
when interacting with the chatbot.

An intent is composed by a name, a set of training sentences and optionally a set of parameters (not necessary now).

The idea here is to give representative examples of each intent so the bot can understand the users messages and
identify their intents.

Usually, the more examples you provide (what we call training data), the better predictions the bot will make on the
users inputs. But note that data quality matters!

.. code:: python

    hello_intent = bot.new_intent('hello_intent', [
        'hello',
        'hi',
    ])

    good_intent = bot.new_intent('good_intent', [
        'good',
        'fine',
    ])

    bad_intent= bot.new_intent('bad_intent', [
        'bad',
        'awful',
    ])

See :doc:`Intents <about/core/intents>` to learn more.

State bodies and transitions
----------------------------

Once we have all the bot components, let's define the state bodies and the transitions.

The body of a state is a python function where you can do anything you want.

It will be run whenever the bot transitions to its state.

It receives the user session as a parameter to read/write user-specific information.

.. note::

    The bot can send messages to the user through the user session (``session.reply("message"))``) or through the
    platform (``websocket_platform.reply(session, "message"))``). There are other kinds of replies which can be platform-specific
    (e.g. sending a picture, reacting to a user message...)

initial_state
~~~~~~~~~~~~~

This state has a transition to *hello_state* that is triggered when the bot receives the *hello_intent*. The state body
is not defined since this state does nothing.

.. code:: python

    initial_state.when_intent_matched_go_to(hello_intent, hello_state)


hello_state
~~~~~~~~~~~

This state can transition to *good_state* or *bad_state* depending on the user response.

.. code:: python

    def hello_body(session: Session):
        session.reply('Hi! How are you?')

    hello_state.set_body(hello_body)
    hello_state.when_intent_matched_go_to(good_intent, good_state)
    hello_state.when_intent_matched_go_to(bad_intent, bad_state)


good_state
~~~~~~~~~~

Here the bot replies according with the last user intent (*good_intent*).

This state has an automatic transition to *initial_state*.

.. code:: python

    def good_body(session: Session):
        session.reply('I am glad to hear that!')

    good_state.set_body(good_body)
    good_state.go_to(initial_state)

bad_state
~~~~~~~~~

Here the bot replies according with the last user intent (*bad_intent*).

This state has an automatic transition to *initial_state*.

.. code:: python

    def bad_body(session: Session):
        session.reply('I am sorry to hear that...')

    bad_state.set_body(bad_body)
    bad_state.go_to(initial_state)

Run the bot
-----------

Everything is ready to run the bot!

.. code:: python

    if __name__ == '__main__':
        bot.run()

Finally, open a terminal and run the bot script:

.. code:: bash

    python greetings_bot.py

Once the bot is trained, a web browser tab with the chatbot interface will pop up and you will be able to start
chatting!

.. note::

    If you encounter the following error:

    .. code:: bash

        ModuleNotFoundError: No module named 'besser'

    You need to add the following code lines at the beginning of the bot script, to add your working directory to the
    Python path:

    .. code:: python

        import sys
        sys.path.append("/Path/to/directory/bot-framework") # Replace with your directory path