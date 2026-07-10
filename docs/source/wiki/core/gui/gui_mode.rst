GUI mode
========

In GUI mode the agent is configured with a GUI model that the client displays as a
persistent, full-page interface. Instead of embedding the UI inside the chat thread,
the layout occupies a dedicated panel — the user can still chat with the agent, but
the GUI remains visible throughout the session and updates dynamically as the
conversation progresses.

This is the right choice when you want the agent to drive an interactive application
— a data dashboard, a wizard, a configuration panel — rather than a purely
conversational flow.

.. figure:: ../../../img/gui_mode_demo.png
   :alt: Example of an agent running in GUI mode

   An agent running in GUI mode: the GUI panel is displayed alongside the chat.

Setting the agent GUI
---------------------

Use :meth:`~baf.core.agent.Agent.set_gui` to attach a GUI model to the agent. This
becomes the **template** from which each new user session receives its own independent
copy:

.. code:: python

   from baf.core.agent import Agent
   from baf.core.gui.agent_gui import AgentGUI

   agent = Agent('dashboard_agent')
   websocket_platform = agent.use_websocket_platform(use_ui=True)

   agent.set_gui(AgentGUI(model))

When a new user connects, the client automatically receives the GUI model and renders
it. No explicit ``reply_gui`` call is needed — the platform sends the initial GUI on
connection.

Session GUI
-----------

Each session keeps its own independent copy of the GUI model in ``session.gui``. You
can read it from any state body to inspect or modify the current user's interface
without affecting other sessions:

.. code:: python

   def some_body(session: Session):
       current_gui: AgentGUI = session.gui

The session's GUI starts as a deep copy of the agent's template (set via
``agent.set_gui``). Changes you make to it are local to that user.

.. warning::

   Mutating ``session.gui`` directly does **not** push the changes to the client.
   Call ``session.set_gui(updated_gui)`` to update the model **and** push it to the
   WebSocket client automatically (see `Updating the GUI dynamically`_ below).

Updating the GUI dynamically
-----------------------------

Call :meth:`~baf.core.session.Session.set_gui` from a state body to replace the
session's GUI and immediately push the new model to the client:

.. code:: python

   def update_body(session: Session):
       new_gui = session.gui               # start from the current GUI
       new_gui.update_component_by_id(     # modify a specific component
           'status_label',
           content=f'Last updated: {datetime.now():%H:%M:%S}'
       )
       session.set_gui(new_gui)            # push to the client

The client receives the updated model and re-renders the interface. The update is
sent as a separate WebSocket message (action ``AGENT_REPLY_GUI_UPDATE``) and does not
appear in the chat history.

AgentGUI helper methods
-----------------------

:class:`~baf.core.gui.agent_gui.AgentGUI` provides a few helpers to work with the
model without having to navigate the BESSER BUML data structures manually.

Finding components
~~~~~~~~~~~~~~~~~~

:meth:`~baf.core.gui.agent_gui.AgentGUI.find_component` returns the **first** element
in the model where a given field matches the target value, or ``None`` if none is found.
:meth:`~baf.core.gui.agent_gui.AgentGUI.find_components` returns a **list** of *all*
matching elements (empty list when there are no matches). Both methods search
recursively through all modules → screens → containers.

The first argument is the field name to inspect; the second is the value to match:

.. code:: python

   # Find by component_id (unique identifier)
   label = session.gui.find_component('component_id', 'status_label')
   if label:
       print(label.content)

   # Find by name
   button = session.gui.find_component('name', 'submit_button')

   # Find all components that share a field value
   all_inputs = session.gui.find_components('type', 'TextInput')

Updating a component
~~~~~~~~~~~~~~~~~~~~

:meth:`~baf.core.gui.agent_gui.AgentGUI.update_component_by_id` finds the component
and sets a list of attributes on it in one call:

.. code:: python

   session.gui.update_component_by_id(
       'progress_bar',
       value=75,
       label='75 %',
   )
   session.set_gui(session.gui)  # push the change

Adding a component
~~~~~~~~~~~~~~~~~~

:meth:`~baf.core.gui.agent_gui.AgentGUI.add_component` inserts a new component into
the model. By default it targets the main screen, but you can aim at a specific
container or screen:

.. code:: python

   from besser.BUML.metamodel.gui import Text

   new_label = Text(name='result_text', content='Calculation complete.')

   # Add to the main screen
   session.gui.add_component(new_label)

   # Add to a specific container (by component_id)
   session.gui.add_component(new_label, parent_id='results_container')

   # Add to a named screen
   session.gui.add_component(new_label, screen_name='dashboard')

   session.set_gui(session.gui)

Getting a screen
~~~~~~~~~~~~~~~~

:meth:`~baf.core.gui.agent_gui.AgentGUI.get_screen` returns a ``Screen`` object by
name, falling back to the main screen (``is_main_page=True``) and then the first
screen if no name is given:

.. code:: python

   home_screen  = session.gui.get_screen()              # main / first screen
   detail_screen = session.gui.get_screen('detail')     # by name

Reacting to GUI events in GUI mode
------------------------------------

Even in GUI mode the user can interact with the GUI components — clicking buttons,
updating form fields, submitting forms. Each interaction generates a
:class:`~baf.library.transition.events.base_events.GUIEvent` that the agent receives
and can use to drive state transitions.

A common pattern is to listen for any GUI event and then update the interface based
on what the user did:

.. code:: python

   from baf.library.transition.events.base_events import GUIEvent

   # Move to an update state whenever any GUI event arrives
   initial_state.when_event(GUIEvent()).go_to(gui_update_state)

   def gui_update_body(session: Session):
       gui = session.gui
       # Inspect the event that triggered this state
       event = session.event
       action = event.event_data.get('action')   # e.g. 'onChange', 'onClick'
       field  = event.event_data.get('name')
       value  = event.event_data.get('value')

       if action == 'onChange':
           gui.update_component_by_id('feedback_text', content=f'You typed: {value}')
           session.set_gui(gui)

   gui_update_state.set_body(gui_update_body)
   gui_update_state.go_to(initial_state)

For form submissions you can use the more focused
:meth:`~baf.core.state.State.when_form_submitted` transition — see
:doc:`../transitions` for details.

Full example
------------

A minimal agent that shows a live-updating dashboard: the GUI displays a label, and
whenever the user sends the text ``"update"``, the agent updates the label with the
current time.

.. code:: python

   import datetime
   from baf.core.agent import Agent
   from baf.core.gui.agent_gui import AgentGUI
   from baf.core.session import Session
   from baf.library.transition.events.base_events import GUIEvent

   agent = Agent('dashboard_agent')
   websocket_platform = agent.use_websocket_platform(use_ui=True)

   # Set the GUI template (model built elsewhere with the BESSER BUML library)
   agent.set_gui(AgentGUI(model))

   # States
   initial_state = agent.new_state('initial_state', initial=True)
   update_state  = agent.new_state('update_state')

   update_intent = agent.new_intent('update_intent', ['update', 'refresh'])

   def initial_body(session: Session):
       session.reply('Dashboard loaded. Say "update" to refresh.')

   initial_state.set_body(initial_body)
   initial_state.when_intent_matched(update_intent).go_to(update_state)

   def update_body(session: Session):
       gui = session.gui
       now = datetime.datetime.now().strftime('%H:%M:%S')
       gui.update_component_by_id('clock_label', content=f'Last update: {now}')
       session.set_gui(gui)
       session.reply(f'Dashboard updated at {now}.')

   update_state.set_body(update_body)
   update_state.go_to(initial_state)

   if __name__ == '__main__':
       agent.run()

API References
--------------

- Agent.set_gui(): :meth:`baf.core.agent.Agent.set_gui`
- AgentGUI: :class:`baf.core.gui.agent_gui.AgentGUI`
- AgentGUI.add_component(): :meth:`baf.core.gui.agent_gui.AgentGUI.add_component`
- AgentGUI.find_component(): :meth:`baf.core.gui.agent_gui.AgentGUI.find_component`
- AgentGUI.find_components(): :meth:`baf.core.gui.agent_gui.AgentGUI.find_components`
- AgentGUI.get_screen(): :meth:`baf.core.gui.agent_gui.AgentGUI.get_screen`
- AgentGUI.update_component_by_id(): :meth:`baf.core.gui.agent_gui.AgentGUI.update_component_by_id`
- GUIEvent: :class:`baf.library.transition.events.base_events.GUIEvent`
- Session.gui: :attr:`baf.core.session.Session.gui`
- Session.set_gui(): :meth:`baf.core.session.Session.set_gui`
- WebSocketPlatform.reply_gui_update(): :meth:`baf.platforms.websocket.websocket_platform.WebSocketPlatform.reply_gui_update`
