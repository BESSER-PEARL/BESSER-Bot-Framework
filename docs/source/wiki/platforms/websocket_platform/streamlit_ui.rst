Streamlit UI
============

We provide a Streamlit UI implementing a WebSocket client to communicate with the agent.

This is how our agent UI looks like:

.. figure:: ../../../img/streamlit_ui_demo.gif
   :alt: WebSocket UI demo

How to use it
-------------

You can run it directly from the agent, by setting it in the websocket_platform:

.. code:: python

    agent = Agent('example_agent')
    ...
    websocket_platform = agent.use_websocket_platform(use_ui=True)

Or you can also run it separately. Just open a terminal on the streamlit UI directory, and run:

.. code:: bash

    streamlit run --server.address localhost --server.port 5000 streamlit_ui.py agent_name localhost 8765
