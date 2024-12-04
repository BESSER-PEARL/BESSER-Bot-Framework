Platforms
=========

An agent has to interact with the users through some communication channel. BBF's platforms wrap all the
necessary code to build the connection between the agent and a communication channel.

All platforms implement the abstract class :class:`~besser.agent.platforms.platform.Platform`. It defines the methods any
platform must have. So, if you would like to create your own platform (and contribute to the BBF
development 🙂), it must implement them according to the platform needs:

- :meth:`~besser.agent.platforms.platform.Platform.initialize`: Initialize the platform. It is called internally when
  you run the agent (:meth:`Agent.run() <besser.agent.core.agent.Agent.run>`). You may need to set some things previously to the
  platform execution.

- :meth:`~besser.agent.platforms.platform.Platform.start`: Start the platform execution. It is called internally when
  you run the agent (:meth:`Agent.run() <besser.agent.core.agent.Agent.run>`).

- :meth:`~besser.agent.platforms.platform.Platform.stop`: Stop the platform. It is called internally when
  you stop the agent (:meth:`Agent.stop() <besser.agent.core.agent.Agent.stop>`).

- :meth:`~besser.agent.platforms.platform.Platform._send`: Send a payload (usually a message) to the user. This is a
  private method. It is called internally by other platform methods, such as the following one.

- :meth:`~besser.agent.platforms.platform.Platform.reply`: Send a textual message to the user.

Additionally, a platform could have specific methods for it, as you can see in our implemented platforms.

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   platforms/websocket_platform
   platforms/telegram_platform
