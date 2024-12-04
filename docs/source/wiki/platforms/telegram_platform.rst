Telegram platform
=================

The Telegram Platform allows an agent to communicate with the users using `Telegram <https://telegram.org/>`_.

Telegram is a great platform for chatbots/agents. You can create a Telegram bot through the
`Bot Father <https://core.telegram.org/bots/tutorial>`_ and then, link it to our BBF agent. This way,
you can define your agent architecture and logics, and then use your Telegram bot as the communication channel.

Our Telegram Platform uses the `python-telegram-bot <https://github.com/python-telegram-bot/python-telegram-bot>`_
library, which is a Telegram Bot API wrapper for Python.

.. figure:: ../../img/telegram_demo.gif
   :alt: Telegram demo

   Example agent using Telegram

.. note::

    There are some properties the agent needs in order to properly set the Telegram connection. More details in the
    :any:`configuration properties <properties-telegram_platform>` documentation.

How to use it
-------------

After you instantiate your agent, simply call the following function:

.. code:: python

    agent = Agent('example_bot')
    ...
    telegram_platform = agent.use_telegram_platform()

After that, you can use the platform to send different kinds of messages to the user
(from :any:`state bodies<state-body>`):

- Text messages (strings):

.. code:: python

    telegram_platform.reply(session, 'Hello!')

- Files:

.. code:: python

    file = File(file_name="name", file_type="type", file_base64="file_base64")
    telegram_platform.reply_file(session, file, message='Optional caption')

- Images:

.. code:: python

    telegram_platform.reply_image(file=f, session=session, message='Optional caption') # the file must be an image

- Locations:

.. code:: python

    latitude, longitude = 49.50177449302207, 5.94862573528648
    telegram_platform.reply_location(session, latitude, longitude)


.. note::

    The agent cannot detect when a user opens the Telegram chat window. Therefore, to start the conversation, it is needed
    a first message to "wake the agent up". After that, it will start running the initial state.

⏳ We are working on other replies (files, media, charts...). They will be available soon, stay tuned!

Handlers
--------

The python-telegram-bot library (Telegram Bot API Python wrapper under our Telegram Platform) uses
`handlers <https://docs.python-telegram-bot.org/en/latest/telegram.ext.handlers-tree.html>`_ to handle
bot updates (e.g., the user sends a text message, an image, a command, etc.). Our Telegram Platform interface allows
you to add custom handlers to your agent, so this feature is not lost when using BBF.

This is an example handler function that will be executed when the agent receives the ``/help`` command:

.. code:: python

    from telegram import Update
    from telegram.ext import CommandHandler, ContextTypes
    ...
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session_id = str(update.effective_chat.id)
        session = agent.get_or_create_session(session_id)
        session.reply('Please introduce a number between 1 and 10')

    help_handler = CommandHandler('help', help)

    telegram_platform.add_handler(help_handler)

.. note::

    You can take the built-in handlers as a reference to create handlers integrated with the agent.

Our Telegram Platform has the following built in handlers:

- One to handle all user text messages (that simply captures the messages and sends them to the agent).
- A *reset* handler that resets the agent when the user writes the command ``/reset``.
- A voice message handler (you need to set the :doc:`../nlp/speech2text` component to enable voice messages)
- A file handler to receive files from the user
- An image handler to receive images from the user (images are a subset of files)


Telegram Wrapper
----------------

The BBF Telegram Platform wraps some functionalities of the python-telegram-bot library (such as adding handlers or
replying messages, files or locations), but not all of them.

In order to use other features not included in BBF yet, we included a `__getattr__` function in the TelegramPlatform
class. It forwards the method calls not implemented in TelegramPlatform to the underlying Telegram bot
(`ExtBot <https://docs.python-telegram-bot.org/en/v20.6/telegram.ext.extbot.html>`_ class, which is an extension of the
`Bot <https://docs.python-telegram-bot.org/en/v20.6/telegram.bot.html>`_ class).

**That means you can call any function from the TelegramPlatform as you would do in the Telegram bot!**

Let's see an example.

You could use `send_audio <https://docs.python-telegram-bot.org/en/v20.6/telegram.bot.html#telegram.Bot.send_audio>`_
to send audios to the user. Since this is not integrated in our TelegramPlatform, you can simply call it and it will be
forwarded:

.. code:: python

    def example_body(session: Session):
        # The session id is the Telegram chat_id
        telegram_platform.send_audio(session.id, my_audio, title='Hello World')

Note that the TelegramPlatform wrappers also involve other actions. For instance, when the agent replies a message, it can be
added to a chat history :doc:`database <../db/monitoring_db>`. You can also customize what is done when calling any function.
You could update the chat history to record the audio messages, either adding the audio or simply a log message:

.. code:: python

    from datetime import datetime
    from besser.agent.core.message import Message, MessageType

    def custom_send_audio(session: Session, audio):
        message = Message(MessageType.AUDIO, audio, is_user=False, timestamp=datetime.now())
        session.save_message(message)
        telegram_platform.send_audio(session.id, audio, title='Hello World')

    def example_body(session: Session):
        custom_send_audio(session, audio)


API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.get_or_create_session(): :meth:`besser.agent.core.agent.Agent.get_or_create_session`
- Agent.use_telegram_platform(): :meth:`besser.agent.core.agent.Agent.use_telegram_platform`
- File: :class:`besser.agent.core.file.File`
- Message: :class:`besser.agent.core.message.Message`
- MessageType: :class:`besser.agent.core.message.MessageType`
- TelegramPlatform: :class:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform`
- TelegramPlatform.add_handler(): :meth:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform.add_handler`
- TelegramPlatform.reply(): :meth:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform.reply`
- TelegramPlatform.reply_file(): :meth:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform.reply_file`
- TelegramPlatform.reply_image(): :meth:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform.reply_image`
- TelegramPlatform.reply_location(): :meth:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform.reply_location`
