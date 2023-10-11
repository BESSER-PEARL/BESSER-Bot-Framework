Configuration properties
========================

A bot needs some parameters to be set to properly work. In this section, you will find all of them, and we will explain
you how to load them in the bot.

A bot :class:`Property <besser.bot.core.property.Property>` has a section, a name, a type and a default value
(for when the property is not defined by the bot developer).


Loading properties
------------------

You can define your bot properties in 2 different ways:

- **Using a configuration `.ini` file:** It is a file containing all the bot properties. Let's see an example
  ``config.ini`` file:

.. literalinclude:: ../../../besser/bot/test/examples/config.ini

Now you have to load the file into the chatbot:

.. code:: python

    bot = Bot('example_bot')
    bot.load_properties('config.ini')

- **Setting individual properties:** You can also set (and get) properties individually from the bot code.

.. code:: python

    from besser.bot.nlp import NLP_LANGUAGE
    ...
    bot = Bot('example_bot')
    bot.set_property(NLP_LANGUAGE, 'es')
    ...
    language = bot.get_property(NLP_LANGUAGE)

.. note::

    When you try to get a property that has not been previously set, it will return its default value.

You can also create your own properties:

.. code:: python

    from besser.bot.core.property import Property
    ...
    FACEBOOK_PROFILE = Property('facebook', 'facebook.profile', str, 'https://www.facebook.com/foo')
    ...
    bot.set_property(FACEBOOK_PROFILE, 'https://www.facebook.com/john_doe')

Next, let's see all the built in properties, divided by sections.

NLP
---

.. automodule:: besser.bot.nlp
   :members:

.. _properties-websocket_platform:

WebSocket Platform
------------------

.. automodule:: besser.bot.platforms.websocket
   :members:

.. _properties-telegram_platform:

Telegram Platform
------------------

.. automodule:: besser.bot.platforms.telegram
   :members:

API References
--------------

- Bot: :class:`besser.bot.core.bot.Bot`
- Bot.set_property(): :meth:`besser.bot.core.bot.Bot.set_property`
- Bot.get_property(): :meth:`besser.bot.core.bot.Bot.get_property`
- Property: :class:`besser.bot.core.property.Property`
