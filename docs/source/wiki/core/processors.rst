Processor
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

        def process(self, session: 'Session', message: Any) -> Any:
            # Custom processing logic goes here
            processed_message = message.lower()  # Example: convert message to lowercase
            return processed_message

    # Usage
    my_processor = MyCustomProcessor()
    processed_message = my_processor.process(session, "HELLO WORLD")
    print(processed_message)  # Output: "hello world"

The example demonstrates the implementation of a `MyCustomProcessor` that converts all incoming messages to lowercase.

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

  Parameters:
  
  - **session** (`Session`): The current session object, containing the state and context of the bot-user interaction.
  - **message** (`Any`): The message to be processed.

  Returns:
  
  - **Any**: The processed message. The return type can vary depending on the implementation.

Raising Exceptions
------------------

The following exceptions may be raised:

- **ProcessorTargetUndefined**: Raised if a `Processor` is created without specifying either `user_messages` or `bot_messages` as `True`.

API References
--------------

- Processor: :class:`besser.bot.processors.processor.Processor`
- Processor.process(): :meth:`besser.bot.processors.processor.Processor.process`
- Session: :class:`besser.bot.core.session.Session`
- ProcessorTargetUndefined: :class:`besser.bot.exceptions.exceptions.ProcessorTargetUndefined`
