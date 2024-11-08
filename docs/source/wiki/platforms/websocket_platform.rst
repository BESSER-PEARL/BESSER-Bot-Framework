WebSocket platform
==================

The WebSocket Platform allows a bot to communicate with the users using the
`WebSocket <https://en.wikipedia.org/wiki/WebSocket>`_ bidirectional communications protocol.

This platform implements the WebSocket server, and it can establish connection with a client, allowing the
bidirectional communication between server and client (i.e. sending and receiving messages).

The next figure shows how this connection works:

.. figure:: ../../img/websocket_diagram.png
   :alt: Intent diagram

   Figure illustrating the WebSocket protocol.

User Interface

BBF comes with some User Interfaces (WebSocket clients) to use the WebSocket platform.

Of course, you are free to use or create your own UI as long as it has a WebSocket client that connects to the bot's WebSocket server.

.. toctree::
   :maxdepth: 1

   websocket_platform/streamlit_ui
   websocket_platform/chat_widget

(Their source code can be found in the besser.bot.platforms.websocket package)

.. note::

    There are some properties the bot needs in order to properly set the WebSocket connection. More details in the
    :any:`configuration properties <properties-websocket_platform>` documentation.

How to use it
-------------

After you instantiate your bot, simply call the following function:

.. code:: python

    bot = Bot('example_bot')
    ...
    websocket_platform = bot.use_websocket_platform(use_ui=True)

If you don't want to use the UI we provide, simply set use_ui to False.

After that, you can use the platform to send different kinds of messages to the user
(from :any:`state bodies<state-body>`):

- Text messages (strings):

.. code:: python

    websocket_platform.reply(session, 'Hello!')

- Text messages in `Markdown <https://www.markdownguide.org/>`_ format:

.. code:: python

    websocket_platform.reply_markdown(session, """
        # Welcome to the chatbot experience
        ## Section 1
        - one
        - two
    """)

- Text messages in `HTML <https://en.wikipedia.org/wiki/HTML>`_ format:

.. code:: python

    websocket_platform.reply_html(session, """
        <h1>Title</h1>
        <ul>
            <li>Apples</li>
            <li>Bananas</li>
            <li>Cherries</li>
        </ul>
    """)

- Pandas `DataFrames <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_:

.. code:: python

    websocket_platform.reply_dataframe(session, df)

- List of options (buttons): Display a list of options as buttons and let the user choose one

.. code:: python

    websocket.reply_options(session, ['Yes', 'No'])

- Plotly `figure <https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html>`_:

.. code:: python

    websocket_platform.reply_plotly(session, plot)

- Files:

.. code:: python

    file = File(file_name="name", file_type="type", file_base64="file_base64")
    websocket_platform.reply_file(session, file)

- Locations:

.. code:: python

    latitude, longitude = 49.50177449302207, 5.94862573528648
    websocket_platform.reply_location(session, latitude, longitude)

- :doc:`../nlp/rag` Messages:

.. code:: python

    rag_message: RAGMessage = session.run_rag()
    websocket_platform.reply_rag(session, rag_message)

⏳ We are working on other replies (files, media, charts...). They will be available soon, stay tuned!

The WebSocket platform allows the following kinds of user messages:

- Text messages
- Voice messages
- Files

API References
--------------

- Bot: :class:`besser.bot.core.bot.Bot`
- Bot.use_websocket_platform(): :meth:`besser.bot.core.bot.Bot.use_websocket_platform`
- WebSocketPlatform: :class:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform`
- WebSocketPlatform.reply(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply`
- WebSocketPlatform.reply_dataframe(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply_dataframe`
- WebSocketPlatform.reply_file(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply_file`
- WebSocketPlatform.reply_location(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply_location`
- WebSocketPlatform.reply_options(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply_options`
- WebSocketPlatform.reply_plotly(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply_plotly`
- WebSocketPlatform.reply_rag(): :meth:`besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform.reply_rag`
