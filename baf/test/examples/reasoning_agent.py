# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

"""Reasoning-state example agent.

Demonstrates the new BAF reasoning extension:
    * markdown skills loaded from a folder
    * Python tools loaded from a sibling module + decorator-registered tool
    * a workspace pointing at the example directory itself, so the LLM can
      browse and read the example files on demand
    * a single predefined reasoning state wired up with ``use_reasoning_state``

Run with the existing config file (``config_marcos.yaml``) and the OpenAI key
already used by the other examples.
"""

import logging
import os

from baf.core.agent import Agent
from baf.exceptions.logger import logger
from baf.library.state import new_reasoning_state
from baf.nlp.llm.llm_openai_api import LLMOpenAI
from baf.platforms.websocket import WEBSOCKET_PORT

# Configure the logging module (optional)
logger.setLevel(logging.DEBUG)

# Create the agent
agent = Agent("reasoning_agent")
# Load agent properties stored in a dedicated file
agent.load_properties("config_marcos.yaml")
agent.set_property(WEBSOCKET_PORT, 8775)
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# Create the LLM (must support tool-calling — LLMOpenAI does).
gpt = LLMOpenAI(
    agent=agent,
    name="gpt-5.4-mini",
    parameters={},
    num_previous_messages=10,
)

# --- Skills (markdown files) ---------------------------------------------- #

_HERE = os.path.dirname(os.path.abspath(__file__))
agent.load_skills(os.path.join(_HERE, "reasoning_skills"))
agent.new_skill(
    "Always greet the user by name when they introduce themselves.",
    name="GreetByName",
)

# --- Tools (Python callables) --------------------------------------------- #

# Bulk-register every public callable defined in reasoning_tools.py.
agent.load_tools(os.path.join(_HERE, "reasoning_tools.py"))


# Add a one-off tool with the decorator form.
@agent.tool
def echo(text: str) -> str:
    """Echo the user-supplied text back, unchanged."""
    return text


# --- Workspace (filesystem the agent can browse) -------------------------- #

# Point the agent at the examples folder so it can list and read example files
# on demand. Replace with any folder you want the agent to explore.
agent.new_workspace(_HERE + "\\workspace", name="cinema", writable=True)

# --- Reasoning state ------------------------------------------------------ #

# Single predefined state that runs the LLM-driven think→act→observe loop.
reasoning_state = new_reasoning_state(agent=agent, llm=gpt, max_steps=30)
reasoning_state.when_event().go_to(reasoning_state)


# RUN APPLICATION

if __name__ == "__main__":
    agent.run()
