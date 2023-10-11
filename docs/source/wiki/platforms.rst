Platforms
=========

A chatbot has to interact with the users through some communication channel. Bot Framework's platforms wrap all the
necessary code to build the connection between the bot and a communication channel.

All platforms implement the abstract class :class:`~besser.bot.platforms.platform.Platform`. It defines the methods any
platform must have. So, if you would like to create your own platform (and contribute to the Bot Framework
development 🙂), it must implement them:

- :meth:`~besser.bot.platforms.platform.Platform._send`: Send a payload (usually a message) to the user. This is a
  private method. It is called internally by other platform methods, such as the following one.

- :meth:`~besser.bot.platforms.platform.Platform.reply`: Send a textual message to the user.

- :meth:`~besser.bot.platforms.platform.Platform.run`: Start the platform. It is called internally when
  you run the bot (:meth:`Bot.run() <besser.bot.core.bot.Bot.run>`).


Additionally, a platform could have specific methods for it, as you can see in our implemented platforms.

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   platforms/websocket_platform
   platforms/telegram_platform
