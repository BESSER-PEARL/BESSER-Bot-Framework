LLM
===

A Large Language Model (LLM) is a type of Artificial Intelligence that is designed to understand and generate human
language. These models are trained on vast amounts of text data and use complex algorithms, particularly deep learning
techniques, to learn the patterns and structures of language.

.. figure:: ../../img/llm_diagram.png
   :alt: LLM diagram

   Example tasks that can be done with an LLM.

There are multiple kinds of LLMs, so choosing one may become a complicated task if we are not familiar with them.
Moreover, the NLP field moves at a very fast pace, so LLMs become obsolete quite fast (which is actually good because
it means something better has been created out there!).

**Some important things to consider when selecting an LLM:**

- **Proprietary** (e.g., OpenAI) vs **Open-Source** (HuggingFace is the biggest repository): Most proprietary LLMs are good and
  reliable, although it is rare to find good free options.
- **Locally deployed vs through API**: You can use an LLM deployed on your premises, but depending on its size it may be
  cheaper to pay for an API (The HuggingFace Inference API offers some LLMs for free)
- **Latency**: the time the LLM spends to generate the answers.
- **Size**: Smaller LLMs (e.g., 2 billion parameters) tend to be more limited than bigger ones (e.g., 70 billion parameters),
  although they may be enough if you want to deploy locally and for specific tasks.

How to use
----------

Let's see how to seamlessly integrate an LLM into our bot. You can also check the :doc:`../../examples/llm_bot` for a complete example.

We are going to create an LLMOpenAI:

.. code:: python

    from besser.bot.nlp.llm.llm_openai_api import LLMOpenAI

    bot = Bot('example_bot')

    gpt = LLMOpenAI(bot=bot, name='gpt-4o-mini')

This LLM can be used within any bot state (in both the body and the fallback body):

.. code:: python

    def answer_body(session: Session):
        answer = gpt.predict(session.message) # Predicts the output for the given input (the user message)
        session.reply(answer)

There are plenty of possibilities to take advantage of LLMs in a chatbot. The previous is a very simple use case, but
we can do more advanced tasks through prompt engineering.

Available LLMs
--------------

BBF comes with LLM wrappers that provide the necessary methods to use them. All LLM wrappers must implement the
:class:`~besser.bot.nlp.llm.llm.LLM` class, which comes with the following methods to be implemented:

- :meth:`~besser.bot.nlp.llm.llm.LLM.initialize`: Initialize the LLM.
- :meth:`~besser.bot.nlp.llm.llm.LLM.predict`: Generate the output for a given input.
- :meth:`~besser.bot.nlp.llm.llm.LLM.chat`: Simulate a conversation. The LLM receives previous messages to be able to continue with a conversation. Not mandatory to implement.
- :meth:`~besser.bot.nlp.llm.llm.LLM.intent_classification`: Predict the intent of a given message (it allows the
  :any:`llm-intent-classifier` to use this LLM). Not mandatory to implement.

These are the currently available LLM wrappers in BBF:

- :class:`~besser.bot.nlp.llm.llm_openai_api.LLMOpenAI`: For `OpenAI <https://platform.openai.com/docs/models>`_ LLMs
- :class:`~besser.bot.nlp.llm.llm_huggingface.LLMHuggingFace`: For `HuggingFace <https://huggingface.co/>`_ LLMs locally deployed
- :class:`~besser.bot.nlp.llm.llm_huggingface_api.LLMHuggingFaceAPI`: For HuggingFace LLMs, through its `Inference API <https://huggingface.co/docs/api-inference>`_
- :class:`~besser.bot.nlp.llm.llm_replicate_api.LLMReplicate`: For `Replicate <https://replicate.com/>`_ LLMs, through its API

API References
--------------

- Bot: :class:`besser.bot.core.bot.Bot`
- LLM: :class:`besser.bot.nlp.llm.llm.LLM`
- LLM.predict: :meth:`besser.bot.nlp.llm.llm.LLM.predict`
- LLMHuggingFace: :class:`besser.bot.nlp.llm.llm_huggingface.LLMHuggingFace`:
- LLMHuggingFaceAPI: :class:`besser.bot.nlp.llm.llm_huggingface_api.LLMHuggingFaceAPI`:
- LLMOpenAI: :class:`besser.bot.nlp.llm.llm_openai_api.LLMOpenAI`
- LLMReplicate: :class:`besser.bot.nlp.llm.llm_replicate_api.LLMReplicate`:
- Session: :class:`besser.bot.core.session.Session`
- Session.reply(): :meth:`besser.bot.core.session.Session.reply`
