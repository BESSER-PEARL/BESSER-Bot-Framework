from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from besser.agent.core.session import Session
from besser.agent.exceptions.exceptions import ProcessorTargetUndefined

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class Processor(ABC):
    """The processor abstract class.

    A processor defines the processing a user or agent message goes through.

    This class serves as a template to implement processors.

    Args:
        agent (Agent): The agent the processor belongs to
        user_messages (bool): whether the processor should be applied to user messages
        agent_messages (bool): whether the processor should be applied to agent messages

    Attributes:
        agent (Agent): The agent the processor belongs to
        user_messages (bool): whether the processor should be applied to user messages
        agent_messages (bool): whether the processor should be applied to agent messages
    """

    def __init__(self, agent: 'Agent', user_messages: bool = False, agent_messages: bool = False):
        if not (user_messages or agent_messages):
            raise ProcessorTargetUndefined(self)
        self.agent = agent
        self.user_messages = user_messages
        self.agent_messages = agent_messages
        self.agent.processors.append(self)

    @abstractmethod
    def process(self, session: 'Session', message: Any) -> Any:
        """Abstract method to process a message.

        Args:
            session (Session): the current session
            message (Any): the message to be processed

        Returns:
            Any: the processed message
        """
        pass
