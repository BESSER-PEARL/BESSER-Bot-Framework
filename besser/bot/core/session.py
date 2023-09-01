import logging
from typing import Any, TYPE_CHECKING

from besser.bot.core.transition import Transition
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.core.state import State
    from besser.bot.platforms.platform import Platform


class Session:
    """
    A user session in a bot execution.

    When a user starts interacting with a bot, a session is assigned to him/her to store user related information, such
    as the current state of the bot, the conversation history, the detected intent with its parameters or any user's
    private data. A session can be accessed from the body of the states to read/write user information.

    :param session_id: the session id, which must unique among all bot sessions
    :type session_id: str
    :param bot: the bot the session belongs to
    :type bot: Bot
    :param platform: the platform where the session has been created
    :type platform: Platform

    :ivar str _id: the session id, which must unique among all bot sessions
    :ivar str _bot: the bot the session belongs to
    :ivar str _platform: the platform where the session has been created
    :ivar str _current_state: the current state in the bot for this session
    :ivar str _dictionary: storage of private data for this session
    :ivar str _message: the last message sent to the bot by this session
    :ivar str predicted_intent: the last predicted intent for this session
    :ivar str chat_history: the session chat history
    """

    def __init__(
            self,
            session_id: str,
            bot: 'Bot',
            platform: 'Platform',
    ):
        self._id: str = session_id
        self._bot: 'Bot' = bot
        self._platform: 'Platform' = platform
        self._current_state: 'State' = self._bot.initial_state()
        self._dictionary: dict[str, Any] = {}
        self._message: str or None = None
        self.predicted_intent: IntentClassifierPrediction or None = None
        self.chat_history: list[tuple[str, int]] = []

    @property
    def id(self):
        """
        Get the session id.

        :return: The session id
        """
        return self._id

    @property
    def platform(self):
        """
        Get the session platform.

        :return: The session platform
        """
        return self._platform

    @property
    def current_state(self):
        """
        Get the current bot state of the session.

        :return: The current bot state of the session.
        """
        return self._current_state

    @property
    def message(self):
        """
        Get the last message sent to the bot.

        :return: The message
        """
        return self._message

    @message.setter
    def message(self, message):
        """
        Set the last message sent to the bot.
        """
        self.chat_history.append((message, 1))
        self._message = message

    def set(self, key: str, value: Any) -> None:
        """
        Set an entry to the session private data storage.

        :param key: the entry key
        :type key: str
        :param value: the entry value
        :type value: Any
        :return:
        :rtype:
        """
        self._dictionary[key] = value

    def get(self, key: str) -> Any:
        """
        Get an entry of the session private data storage.

        :param key: the entry key
        :type key: str
        :return: the entry value, or None if the key does not exist
        :rtype: Any
        """
        if key not in self._dictionary:
            return None
        return self._dictionary[key]

    def delete(self, key: str) -> None:
        """
        Delete an entry of the session private data storage.

        :param key: the entry key
        :type key: str
        :return:
        :rtype:
        """
        del self._dictionary[key]

    def move(self, transition: Transition):
        """
        Move to another bot state.

        :param transition: the transition that points to the bot state to move
        :type transition: Transition
        :return:
        :rtype:
        """
        logging.info(transition.log())
        self._current_state = transition.dest
        self._current_state.run(self)

    def reply(self, message: str) -> None:
        """
        A bot message (a usually a reply to a user message) is sent to the session platform to show it to the user.

        :param message: the bot reply
        :type message: str
        :return:
        :rtype:
        """
        # Multi-platform
        self._platform.reply(self, message)
