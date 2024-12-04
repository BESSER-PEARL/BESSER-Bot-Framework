Chat widget
===========

The chat widget UI allows to integrate an agent in any webpage. It is located in a window corner, expanded/hidden when clicking on an icon.

This is how our agent UI looks like:

.. figure:: ../../../img/chat_widget_demo.gif
   :alt: Chat Widget demo
   :scale: 70%

Parameters
----------

The file data/args.json contains parameters you can set to customize the chat widget (websocket address, agent icon, colors, ...)

How to use it
-------------

Just go to the chat_widget directory and open the **index.html** file.

.. note::

    The parameters can only be read from the JSON file when running the interface from a server, not from the file system.

    You can create a simple server by running the following in the chat widget directory:

    .. code:: bash

        python -m http.server

    This will serve your files at http://localhost:8000

    If you want to run it from the file system, you will have to hardcode the parameters (instead of loading them from
    an external file, just write your desired values in the renderChatWidget function in the js/script.js file)

To integrate the chat widget in a real webpage, just copy the content in index.html into the html of your webpage.
Make sure to include the other directories in the webpage dependencies, as they contain the chat widget code.
