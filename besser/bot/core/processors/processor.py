from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from besser.bot.core.session import Session
from besser.bot.exceptions.exceptions import ProcessorTargetUndefined

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class Processor(ABC):
    """The processor abstract class.

    A processor defines the processing a user or bot message goes through.

    This class serves as a template to implement processors.

    Args:
        bot (Bot): The bot the processor belongs to
        user_messages (bool): whether the processor should be applied to user messages
        bot_messages (bool): whether the processor should be applied to bot messages

    Attributes:
        bot (Bot): The bot the processor belongs to
        user_messages (bool): whether the processor should be applied to user messages
        bot_messages (bool): whether the processor should be applied to bot messages
    """

    def __init__(self, bot: 'Bot', user_messages: bool = False, bot_messages: bool = False):
        if not (user_messages or bot_messages):
            raise ProcessorTargetUndefined(self)
        self.bot = bot
        self.user_messages = user_messages
        self.bot_messages = bot_messages
        self.bot.processors.append(self)

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
