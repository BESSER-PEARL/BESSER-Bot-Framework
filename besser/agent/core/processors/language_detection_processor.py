from typing import TYPE_CHECKING

from langdetect import detect

from besser.agent.core.processors.processor import Processor
from besser.agent.core.session import Session

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class LanguageDetectionProcessor(Processor):
    """The LanguageDetectionProcessor returns the spoken language in a given message.

    This processor leverages the langdetect library to predict the language.

    Args:
        agent (Agent): The agent the processor belongs to
        user_messages (bool): Whether the processor should be applied to user messages
        agent_messages (bool): Whether the processor should be applied to agent messages

    Attributes:
        agent (Agent): The agent the processor belongs to
        user_messages (bool): Whether the processor should be applied to user messages
        agent_messages (bool): Whether the processor should be applied to agent messages
    """
    def __init__(self, agent: 'Agent', user_messages: bool = False, agent_messages: bool = False):
        super().__init__(agent=agent, user_messages=user_messages, agent_messages=agent_messages)

    def process(self, session: Session, message: str) -> str:
        """Method to process a message and predict the message's language.

        The detected language will be stored as a session parameter. The key is "detected_language".

        Args:
            session (Session): the current session
            message (str): the message to be processed

        Returns:
            str: the processed message
        """
        lang = detect(message)
        session.set('detected_language', lang)
        return message
