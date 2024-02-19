Telegram platform
=================

The Telegram Platform allows a bot to communicate with the users using `Telegram <https://telegram.org/>`_.

Telegram is a great platform for chatbots. You can create a Telegram bot through the
`Bot Father <https://core.telegram.org/bots/tutorial>`_ and then, link it to our BBF chatbot. This way,
you can define your chatbot architecture and logics, and then use your Telegram bot as the communication channel.

Our Telegram Platform uses the `python-telegram-bot <https://github.com/python-telegram-bot/python-telegram-bot>`_
library, which is a Telegram Bot API wrapper for Python.

.. figure:: ../../img/telegram_demo.gif
   :alt: Telegram demo

   Example chatbot using Telegram

.. note::

    There are some properties the bot needs in order to properly set the Telegram connection. More details in the
    :any:`configuration properties <properties-telegram_platform>` documentation.

How to use it
-------------

After you instantiate your bot, simply call the following function:

.. code:: python

    bot = Bot('example_bot')
    ...
    telegram_platform = bot.use_telegram_platform()

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

.. note::

    The bot cannot detect when a user opens the Telegram chat window. Therefore, to start the conversation, it is needed
    a first message to "wake the bot up". After that, it will start running the initial state.

⏳ We are working on other replies (files, media, charts...). They will be available soon, stay tuned!

Handlers
--------

The python-telegram-bot library (Telegram Bot API Python wrapper under our Telegram Platform) uses
`handlers <https://docs.python-telegram-bot.org/en/latest/telegram.ext.handlers-tree.html>`_ to handle
bot updates (e.g., the user sends a text message, an image, a command, etc.). Our Telegram Platform interface allows
you to add custom handlers to your bot, so this feature is not lost when using BBF.

This is an example handler function that will be executed when bot receives the ``/help`` command:

.. code:: python

    from telegram import Update
    from telegram.ext import CommandHandler, ContextTypes
    ...
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session_id = str(update.effective_chat.id)
        session = bot.get_session(session_id)
        session.reply('Please introduce a number between 1 and 10')

    help_handler = CommandHandler('help', help)

    telegram_platform.add_handler(help_handler)

Our Telegram Platform has the following built in handlers:

- One to handle all user text messages (that simply captures the messages and sends them to the bot).
- A *reset* handler that resets the bot when the user writes the command ``/reset``.
- A voice message handler (you need to set the :doc:`../nlp/speech2text` component to enable voice messages)
- A file handler to receive files from the user
- An image handler to receive images from the user (images are a subset of files)


API References
--------------

- Bot: :class:`besser.bot.core.bot.Bot`
- Bot.get_session(): :meth:`besser.bot.core.bot.Bot.get_session`
- Bot.use_telegram_platform(): :meth:`besser.bot.core.bot.Bot.use_telegram_platform`
- File: :class:`besser.bot.core.file.File`
- TelegramPlatform: :class:`besser.bot.platforms.telegram.telegram_platform.TelegramPlatform`
- TelegramPlatform.add_handler(): :meth:`besser.bot.platforms.telegram.telegram_platform.TelegramPlatform.add_handler`
- TelegramPlatform.reply(): :meth:`besser.bot.platforms.telegram.telegram_platform.TelegramPlatform.reply`
- TelegramPlatform.reply_file(): :meth:`besser.bot.platforms.telegram.telegram_platform.TelegramPlatform.reply_file`
- TelegramPlatform.reply_image(): :meth:`besser.bot.platforms.telegram.telegram_platform.TelegramPlatform.reply_image`
