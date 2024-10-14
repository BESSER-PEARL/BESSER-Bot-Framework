from abc import ABC, abstractmethod
from typing import Any

from besser.bot.core.session import Session
from besser.bot.exceptions.exceptions import ProcessorTargetUndefined


class Processor(ABC):
    """The processor abstract class.

    A processor defines the processing a user or bot message goes through.

    This class serves as a template to implement processors.

    Attributes:
        user_messages (bool): whether the processor should be applied to user messages
        bot_messages (bool): whether the processor should be applied to bot messages
    """

    def __init__(self, user_messages: bool = False, bot_messages: bool = False):
        self.user_messages = user_messages
        self.bot_messages = bot_messages
        if not (user_messages or bot_messages):
            raise ProcessorTargetUndefined()

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
