Named Entity Recognition
========================

NER is a Natural Language Processing task that involves identifying and categorizing entities within a text into
predefined categories such as the names of persons, organizations, locations, dates, etc.

In the :doc:`entities wiki <../core/entities>`, you have seen how to create your own entities, which then are embedded
into :any:`intent parameters<intents-with-parameters>`. The NER component of an agent will be in charge of recognize
them within the user messages.

Simple NER
----------

This is the NER used by the :any:`simple-intent-classifier`. It extracts parameters from the user messages (only when
using intents with parameters).

It is a simple algorithm that gets all possible parameter's values and checks if they are present in the messages, thus
it will only be able to successfully recognize entities when there is an **exact match** with one of the parameter values.

For instance, if an entity 'sport' has a value 'football', and the user writes 'I like foot ball', there will be no
parameter matching since 'foot ball' is not a value in 'sport' ('football' is)

The Simple NER can also recognize :any:`base-entities`, which don't have a predefined set of values and are more generic.

LLM NER
-------

The :any:`llm-intent-classifier` does also the NER task, extracting the possible parameters in a user message.
In comparison with the Simple NER, this NER is able to recognize parameters **without exactly matching an entity value**.

For instance, given an entity 'sport' with a value 'football' and with no synonyms, if the user writes
'I like foot ball', the parameter 'football' will probably be recognized. It also works with synonyms (that don't
necessarily have to be defined in the entities). For the sentence 'I like soccer', the LLM NER would probably recognize
'football'.

In addition, with LLM NER you can define your entities without values and **simply add an entity description** (or use a
combination of both). Let's see an example entity:

.. code:: python

    email_entity = agent.new_entity(
        name='email_entity',
        description='An entity containing email addresses',
    )

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.new_entity(): :meth:`besser.agent.core.agent.Agent.new_entity`
