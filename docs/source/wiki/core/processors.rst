Processors
=========

The `Processor` class defines an abstract base class for processing user or bot messages within the system. It serves as a template to implement processors that can modify messages before they are handled by other components.

Overview
--------

Processors are used to define custom processing steps for messages exchanged between users and the bot. They can be applied to either user messages, bot messages, or both.

To implement a custom processor, inherit from the `Processor` class and override the `process` method.

Attributes
----------

- **user_messages** (`bool`): Indicates whether the processor should be applied to user messages.
- **bot_messages** (`bool`): Indicates whether the processor should be applied to bot messages.

A `ProcessorTargetUndefined` exception is raised during initialization if neither `user_messages` nor `bot_messages` is set to `True`.

Usage Example
-------------

Here is an example of how to create a custom processor that processes both user and bot messages:

.. code:: python

    from besser.bot.core.session import Session
    from besser.bot.processors.processor import Processor

    class MyCustomProcessor(Processor):
        def __init__(self):
            super().__init__(user_messages=True, bot_messages=True)

        def process(self, session: 'Session', message: str) -> str:
            # Custom processing logic goes here
            processed_message = message.lower()  # Example: convert message to lowercase
            return processed_message

    # Usage
    # Initialise processor
    my_processor = MyCustomProcessor()
    # Add to a bot
    bot = Bot('greetings_bot')
    # Add processor to bot
    bot.add_processor(my_processor)
    
The example demonstrates the implementation of a `MyCustomProcessor` that converts both the user's messages to the bot and the bot's responses to lowercase.

Methods
-------

`Processor` defines the following methods:

- **__init__(self, user_messages: bool = False, bot_messages: bool = False)**
  
  Initializes a new `Processor` instance.

  Parameters:
  
  - **user_messages** (`bool`): Whether the processor should be applied to user messages. Default is `False`.
  - **bot_messages** (`bool`): Whether the processor should be applied to bot messages. Default is `False`.

  Raises:
  
  - **ProcessorTargetUndefined**: If neither `user_messages` nor `bot_messages` is set to `True`.

- **process(self, session: 'Session', message: Any) -> Any**
  
  Abstract method that processes a message. This method should be overridden in subclasses to define custom processing logic.
  Note that the process method MUST return the processed message, even if no changes were applied.

  Parameters:
  
  - **session** (`Session`): The current session object, containing the state and context of the bot-user interaction.
  - **message** (`Any`): The message to be processed.

  Returns:
  
  - **Any**: The processed message. The return type can vary depending on the implementation.

Raising Exceptions
------------------

The following exceptions may be raised:

- **ProcessorTargetUndefined**: Raised if a `Processor` is created without specifying either `user_messages` or `bot_messages` as `True`.

Available processors
--------------------
This section contains a list of implemented processors.

`Language Detection Processor <https://github.com/BESSER-PEARL/BESSER-Bot-Framework/besser/bot/core/processors/language_detection_processor.py>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This processor attempts to detect the language of given messages by using the `langdetect <https://pypi.org/project/langdetect/>`_ library. 
When processed, the recognized language will be stored as a session variable in ISO 639-1 format and can be fetched with the following call:

.. code:: python

    session.get('detected-lang')


API References
--------------

- Processor: :class:`besser.bot.core.processors.processor.Processor`
- Processor.process(): :meth:`besser.bot.core.processors.processor.Processor.process`
- Session: :class:`besser.bot.core.session.Session`
- ProcessorTargetUndefined: :class:`besser.bot.exceptions.exceptions.ProcessorTargetUndefined`
