Configuration properties
========================

An agent needs some parameters to be set to properly work. In this section, you will find all of them, and we will explain
you how to load them in the agent.

An agent :class:`Property <besser.agent.core.property.Property>` has a section, a name, a type and a default value
(for when the property is not defined by the agent developer).


Loading properties
------------------

You can define your agent properties in 2 different ways:

- **Using a configuration `.ini` file:** It is a file containing all the agent properties. Let's see an example
  ``config.ini`` file:

.. literalinclude:: ../../../besser/agent/test/examples/config.ini

Now you have to load the file into the agent:

.. code:: python

    agent = Agent('example_agent')
    agent.load_properties('config.ini')

- **Setting individual properties:** You can also set (and get) properties individually from the agent code.

.. code:: python

    from besser.agent.nlp import NLP_LANGUAGE
    ...
    agent = Agent('example_agent')
    agent.set_property(NLP_LANGUAGE, 'es')
    ...
    language = agent.get_property(NLP_LANGUAGE)

.. note::

    When you try to get a property that has not been previously set, it will return its default value.

You can also create your own properties:

.. code:: python

    from besser.agent.core.property import Property
    ...
    FACEBOOK_PROFILE = Property('facebook', 'facebook.profile', str, 'https://www.facebook.com/foo')
    ...
    agent.set_property(FACEBOOK_PROFILE, 'https://www.facebook.com/john_doe')

Next, let's see all the built in properties, divided by sections.

NLP
---

.. automodule:: besser.agent.nlp
   :members:

.. _properties-websocket_platform:

WebSocket Platform
------------------

.. automodule:: besser.agent.platforms.websocket
   :members:

.. _properties-telegram_platform:

Telegram Platform
------------------

.. automodule:: besser.agent.platforms.telegram
   :members:

.. _properties-database:

Database
--------

.. automodule:: besser.agent.db
   :members:

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.set_property(): :meth:`besser.agent.core.agent.Agent.set_property`
- Agent.get_property(): :meth:`besser.agent.core.agent.Agent.get_property`
- Property: :class:`besser.agent.core.property.Property`
