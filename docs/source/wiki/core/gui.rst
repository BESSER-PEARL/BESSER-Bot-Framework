GUI
===

BAF supports rendering rich graphical user interfaces in the browser using the
`BESSER GUIModel <https://besser.readthedocs.io/en/latest/buml_language/model_types/gui.html>`_. This lets
agents go beyond plain text by sending interactive forms, layouts, charts, and
other UI components to the user.

There are two distinct ways to use GUI in BAF:

- **GUI replies** — the agent sends a GUI component as a chat message. The
  interface is rendered inline in the conversation, alongside regular text messages.
  This is ideal for collecting structured input (e.g. a form) or displaying rich
  content at a specific point in the conversation flow.

- **GUI mode** — the agent is configured with a persistent GUI model that the
  client displays as a full interface, separate from the chat area. This is suited
  for agents that drive a dedicated interactive application rather than a purely
  conversational experience.

Both modes rely on the same :class:`~baf.core.gui.agent_gui.AgentGUI` wrapper and
the same underlying ``GUIModel`` from the BESSER BUML library.

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   gui/gui_replies
   gui/gui_mode
