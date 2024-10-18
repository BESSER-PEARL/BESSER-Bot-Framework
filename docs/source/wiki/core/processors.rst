Processors
==========

The `Processor` class defines an abstract base class for processing user or bot messages within the system. It serves as a template to implement processors that can modify messages before they are handled by other components.

Overview
--------

Processors are used to define custom processing steps for messages exchanged between users and the bot. They can be applied to either user messages, bot messages, or both.

To implement a custom processor, inherit from the `Processor` class and override the `process` method.

Creating a custom Processor
---------------------------

Here is an example of how to create a custom processor that processes both user and bot messages:

.. code:: python

    from besser.bot.core.bot import Bot
    from besser.bot.core.session import Session
    from besser.bot.processors.processor import Processor

    class MyCustomProcessor(Processor):
        def __init__(self, bot):
            super().__init__(bot=bot, user_messages=True, bot_messages=True)

        def process(self, session: 'Session', message: str) -> str:
            # Custom processing logic goes here
            processed_message = message.lower()  # Example: convert message to lowercase
            return processed_message

    # Usage
    bot = Bot('greetings_bot')
    # Initialise processor
    my_processor = MyCustomProcessor(bot)

The example demonstrates the implementation of a `MyCustomProcessor` that converts both the user's messages to the bot and the bot's responses to lowercase.

.. note::

    - A processor can also store some information in the user session, see :any:`language-detection-processor` as an example.
    - A processor can use other bot components. For instance, :doc:`LLMs <../nlp/llm>` already defined in the bot can be accessed within the processor.
      If you define a parameter `llm_name` in your processor, it could be accessed within the process method as follows:
      `llm = self.bot.nlp_engine._llms[self.llm_name]`

Methods
-------

`Processor` defines the following methods:

- **__init__(self, user_messages: bool = False, bot_messages: bool = False)**
  
  Initializes a new `Processor` instance.

Parameters:
  
  - **bot** (`Bot`): The bot the processor belongs to.
  - **user_messages** (`bool`): Whether the processor should be applied to user messages. Default is `False`.
  - **bot_messages** (`bool`): Whether the processor should be applied to bot messages. Default is `False`.

Raises:
  
  - **ProcessorTargetUndefined**: If neither `user_messages` nor `bot_messages` is set to `True`.

- **process(self, session: 'Session', message: Any) -> Any**
  
Abstract method that processes a message. This method should be overridden in subclasses to define custom processing logic.

Parameters:
  
  - **session** (`Session`): The current session object, containing the state and context of the bot-user interaction.
  - **message** (`Any`): The message to be processed.

Returns:
  
  - **Any**: The processed message. The return type can vary depending on the implementation.

.. note::

    The process method MUST return the processed message, even if no changes were applied.

Raising Exceptions
------------------

The following exceptions may be raised:

- **ProcessorTargetUndefined**: Raised if a `Processor` is created without specifying either `user_messages` or `bot_messages` as `True`.

Available processors
--------------------
This section contains a list of implemented processors.


.. _language-detection-processor:

LanguageDetectionProcessor
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`LanguageDetectionProcessor <besser.bot.core.processors.language_detection_processor.LanguageDetectionProcessor>`
attempts to detect the language of given messages by using the `langdetect <https://pypi.org/project/langdetect/>`_ library.
When processed, the recognized language will be stored as a session variable in ISO 639-1 format and can be fetched with the following call:

.. code:: python

    session.get('detected_lang')


API References
--------------

- Processor: :class:`besser.bot.core.processors.processor.Processor`
- Processor.process(): :meth:`besser.bot.core.processors.processor.Processor.process`
- Session: :class:`besser.bot.core.session.Session`
- ProcessorTargetUndefined: :class:`besser.bot.exceptions.exceptions.ProcessorTargetUndefined`
