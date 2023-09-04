Your first bot
==============

Before starting, let's import the dependencies.

.. code:: python

    import logging

    from besser.bot.core.bot import Bot
    from besser.bot.core.session import Session

    # Configure the logging module
    logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')


The first step is to create the bot.

.. code:: python

    # Create the bot
    bot = Bot('greetings_bot')
    # Load bot properties stored in a dedicated file
    bot.load_properties('config.ini')
    # Define the platform your chatbot will use
    websocket_platform = bot.use_websocket_platform(use_ui=True)


Now, we are going to create the bot states.

.. code:: python

    s0 = bot.new_state('s0', initial=True)
    hello_state = bot.new_state('hello_state')
    bye_state = bot.new_state('bye_state')


The next step is to define the intents for the bot.

.. code:: python

    hello_intent = bot.new_intent('hello_intent', [
        'hello',
        'hi'
    ])

    bye_intent = bot.new_intent('bye_intent', [
        'bye',
        'goodbye',
        'see you'
    ])


Once we have all the bot components, let's define the state bodies and the transitions.

First, the initial state, s0:

.. code:: python

    def s0_body(session: Session):
        session.reply('Hello!')


    s0.set_body(s0_body)
    s0.when_intent_matched_go_to(hello_intent, hello_state)


Followed by hello_state:

.. code:: python

    def hello_body(session: Session):
        session.reply('Bye!')


    hello_state.set_body(hello_body)
    hello_state.when_intent_matched_go_to(bye_intent, bye_state)


And finally, bye_state:

.. code:: python

    def bye_body(session: Session):
        session.reply('Let\'s start again...')


    bye_state.set_body(bye_body)
    bye_state.go_to(s0)


Everythinh is ready to run the bot!

.. code:: python

    if __name__ == '__main__':
        bot.run()
