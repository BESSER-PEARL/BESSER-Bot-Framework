Processors
==========

The `Processor` class defines an abstract base class for processing user or agent messages within the system. It serves as a template to implement processors that can modify messages before they are handled by other components.

Overview
--------

Processors are used to define custom processing steps for messages exchanged between users and the agent. They can be applied to either user messages, agent messages, or both.

To implement a custom processor, inherit from the `Processor` class and override the `process` method.

Creating a custom Processor
---------------------------

Here is an example of how to create a custom processor that processes both user and agent messages:

.. code:: python

    from besser.agent.core.agent import Agent
    from besser.agent.core.session import Session
    from besser.agent.processors.processor import Processor

    class MyCustomProcessor(Processor):
        def __init__(self, agent):
            super().__init__(agent=agent, user_messages=True, agent_messages=True)

        def process(self, session: 'Session', message: str) -> str:
            # Custom processing logic goes here
            processed_message = message.lower()  # Example: convert message to lowercase
            return processed_message

    # Usage
    agent = Agent('greetings_agent')
    # Initialise processor
    my_processor = MyCustomProcessor(agent)

The example demonstrates the implementation of a `MyCustomProcessor` that converts both the user's messages to the agent and the agent's responses to lowercase.

.. note::

    - A processor can also store some information in the user session, see :any:`language-detection-processor` as an example.
    - A processor can use other agent components. For instance, :doc:`LLMs <../nlp/llm>` already defined in the agent can be accessed within the processor.
      If you define a parameter `llm_name` in your processor, it could be accessed within the process method as follows:
      `llm = self.agent.nlp_engine._llms[self.llm_name]`

Methods
-------

`Processor` defines the following methods:

- **__init__(self, user_messages: bool = False, agent_messages: bool = False)**
  
  Initializes a new `Processor` instance.

Parameters:
  
  - **agent** (`Agent`): The agent the processor belongs to.
  - **user_messages** (`bool`): Whether the processor should be applied to user messages. Default is `False`.
  - **agent_messages** (`bool`): Whether the processor should be applied to agent messages. Default is `False`.

Raises:
  
  - **ProcessorTargetUndefined**: If neither `user_messages` nor `agent_messages` is set to `True`.

- **process(self, session: 'Session', message: Any) -> Any**
  
Abstract method that processes a message. This method should be overridden in subclasses to define custom processing logic.

Parameters:
  
  - **session** (`Session`): The current session object, containing the state and context of the agent-user interaction.
  - **message** (`Any`): The message to be processed.

Returns:
  
  - **Any**: The processed message. The return type can vary depending on the implementation.

.. note::

    The process method MUST return the processed message, even if no changes were applied.

Raising Exceptions
------------------

The following exceptions may be raised:

- **ProcessorTargetUndefined**: Raised if a `Processor` is created without specifying either `user_messages` or `agent_messages` as `True`.

Available processors
--------------------
This section contains a list of implemented processors.


.. _language-detection-processor:

LanguageDetectionProcessor
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`LanguageDetectionProcessor <besser.agent.core.processors.language_detection_processor.LanguageDetectionProcessor>`
attempts to detect the language of given messages by using the `langdetect <https://pypi.org/project/langdetect/>`_ library.
When processed, the recognized language will be stored as a session variable in ISO 639-1 format and can be fetched with the following call:

.. code:: python

    session.get('detected_lang')


.. _user-adaptation-processor:

UserAdaptationProcessor
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`UserAdaptationProcessor <besser.agent.core.processors.user_adaptation_processor.UserAdaptationProcessor>`
attempts to adapt the agent's responses based on the user's profile. The user profile can be added using the following call:

.. code:: python

    processor.add_user_model(user_model)


API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Processor: :class:`besser.agent.core.processors.processor.Processor`
- Processor.process(): :meth:`besser.agent.core.processors.processor.Processor.process`
- Session: :class:`besser.agent.core.session.Session`
- ProcessorTargetUndefined: :class:`besser.agent.exceptions.exceptions.ProcessorTargetUndefined`
