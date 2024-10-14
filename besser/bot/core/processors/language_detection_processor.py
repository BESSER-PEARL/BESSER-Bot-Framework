from langdetect import detect

from besser.bot.core.processors.processor import Processor
from besser.bot.core.session import Session



class LanguageDetectionProcessor(Processor):
    """The LanguageDetectionProcessor returns the spoken language in a given message.

    This processor leverages the landdetect library to predict the language.

    Args:
        user_messages (bool): Whether the processor should be applied to user messages
        bot_messages (bool): Whether the processor should be applied to bot messages

    Attributes:
        user_messages (bool): Whether the processor should be applied to user messages
        bot_messages (bool): Whether the processor should be applied to bot messages
    """
    def __init__(self, user_messages: bool = False, bot_messages: bool = False):
        super().__init__(user_messages=user_messages, bot_messages=bot_messages)

    def process(self, session: Session, message: str) -> str:
        """Method to process a message and predict the message's language.

        The detected language will be stored as a session parameter. The key is "{session.id}-detected-language".

        Args:
            session (Session): the current session
            message (str): the message to be processed

        Returns:
            str: the processed message
        """
        lang = detect(message)
        session.set(f'{session.id}-detected-language', lang)
        return message
