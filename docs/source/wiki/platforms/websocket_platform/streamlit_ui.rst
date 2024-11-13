Streamlit UI
============

We provide a Streamlit UI implementing a WebSocket client to communicate with the bot.

This is how our chatbot UI looks like:

.. figure:: ../../../img/streamlit_ui_demo.gif
   :alt: WebSocket UI demo

How to use it
-------------

You can run it directly from the bot, by setting it in the websocket_platform:

.. code:: python

    bot = Bot('example_bot')
    ...
    websocket_platform = bot.use_websocket_platform(use_ui=True)

Or you can also run it separately. Just open a terminal on the streamlit UI directory, and run:

.. code:: bash

    streamlit run --server.address localhost --server.port 5000 streamlit_ui.py bot_name localhost 8765
