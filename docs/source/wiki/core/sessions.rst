Sessions
========

A chatbot is designed once, and when it is deployed there is not a copy
of it for each user. There is a single chatbot instance. Therefore, we need a way to organize each user context.
Of course, at the same time there can be multiple users, each of them in a different bot state, with different values
for some variables, etc. To handle this, we introduce the Session object.

**A session is an object assigned to each user where it is stored private data.**

If you dig into the BBF's guts, you will see that some functions receive a Session object
as a parameter. That is because these functions can modify the user session. Most of the session processes are done
internally, so you don't need to worry about it.

You are able to to manipulate the user session in 2 places:

- State body functions (see the :any:`state-body` documentation)

.. code:: python

    def example_body(session: Session):
        # Your code here

- Custom events (see the :any:`custom-event-transitions` documentation)

.. code:: python

    def example_event(session: Session, event_params: dict):
        # Your code here

We will stick to the body use case, although the same can be done in events.

To understand how this internally works, we must know that the body function is defined once, and assigned to a state.
Whenever a user moves to a state, this function is executed by the bot, but taking as argument the user session.
This way the bot can read and write user-specific data stored there and it cannot do it with other users data.

Let's see the different things we can do with a user session.

(here we specify the type of each object, although it is not necessary to do it)

.. code:: python

    def example_body(session: Session):
        # We can get the last intent prediction:
        prediction: IntentClassifierPrediction = session.predicted_intent
        # We can get the session id:
        session_id: str =  session.id
        # We can send a message to the user:
        session.reply('Hello!')
        # We can get the chat history:
        # The integer associated to each message identifies the sender (0 = chatbot, 1 = user)
        chat_history: list[tuple[str, int]] = session.chat_history
        # We can set (store) a variable:
        session.set('age', 30)
        # We can get a variable (the return type can be any type):
        age: int = session.get('age')
        # We can delete a variable:
        session.delete('age')
        # Received files are also stored as part of the user sessions: 
        file: File = session.file

API References
--------------

- Session: :class:`besser.bot.core.session.Session`
- Session.delete(): :meth:`besser.bot.core.session.Session.delete`
- Session.get(): :meth:`besser.bot.core.session.Session.get`
- Session.reply(): :meth:`besser.bot.core.session.Session.reply`
- Session.set(): :meth:`besser.bot.core.session.Session.set`
