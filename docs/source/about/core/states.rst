States
======


Global-States
-------------

Global-States are a special kind of states. 
As opposed to normal states, which are only accessible during certain parts of the bot conversation, global-states are accessible from anywhere.
In that sense, we could also talk about global-state-components, which consist of a series of states that is triggered once the first state is accessed.

Let's visualize this by taking a look at a simplified greetings bot example!

.. figure:: ../../img/greetings_bot_diagram.png
   :alt: Greetings bot diagram

   Greetings bot diagram

Now let's say we would want to add a "help" state, which should help the user in case they don't know how to proceed or want additional information.
To avoid adding the single transitions to each state, it is possible to define the "help" state as a global state.
For that purpose, we first define the "help" state as we would any other state: 

.. code:: python

    help_state = bot.new_state('help_state') 


add image here

Currently, it is only possible to trigger a global-state by specifying an Intent that should trigger the state. 
In our case, let's say we prepared an Intent called "**help_intent**".
Now we need to specifiy that "**help_state**" is a global-state:

.. code:: python

    help_state.set_global(help_intent)

What happens now, is that "**help_state**" will be seen as a global-state by our bot.
This results in the necessary transitions being automatically added by the bot: 
add image here

Note that, regarding the bot's actions during the "**help_state**", one can define it as with any other state by setting the body. 

If a user would trigger the "**help_state**", then the bot will move to the "**help_state**", act as specified in the body, and then jump back to the state the user found themselves in when triggering the global-state.
An example could be the following: 

add image here

Of course, one can add more transitions to a global-state. 
Here, we could talk about a global-state-component, which consists of a series of states only accessible once the initial state in the respective global-component has been triggered.

Extending the initial "**help_state**" works just as with any other state by creating new states and adding the necessary transitions. 
E.g. if we would like to add a state that should be entered if the user thanks the bot for helping them, then we add the following lines: 

.. code:: python

    your_welcome_state = bot.new_state('your_welcome_state')
    ...
    help_state.when_intent_matched_go_to(thanks_intent, your_welcome_state)

We could now see the states "**help_state**" and "**your_welcome_state**" as a global-state-component.
Note that, the final transition back to the original state always gets added to the final state of the global-state-component.

.. warning::

   Currently, only linear state sequences are supported for global-state-components.
   Thus, branching in global-states will work arbitrarily

