import inspect
import logging
import traceback
from typing import Callable

from besser.bot.core.bot import Bot
from besser.bot.core.file import File
from besser.bot.core.meta_bot.meta_session import MetaSession
from besser.bot.core.session import Session
from besser.bot.core.state import State
from besser.bot.exceptions.exceptions import MetaBotBodySignatureError, MetaBotPredictionSignatureError
from besser.bot.library.metabot import default_after_bot_prediction, default_body_metabot, default_bot_prediction, \
    default_fallback_body_metabot
from besser.bot.platforms.platform import Platform


class MetaBot(Bot):

    def __init__(self, name: str):
        super().__init__(name)
        self._bots: dict[str, Bot] = {}
        self._free_states: dict[str, list[State]] = {}
        self._bot_prediction: Callable[[MetaSession, str], Bot] = default_bot_prediction
        self._after_bot_prediction: Callable[[MetaSession, Session], None] = default_after_bot_prediction
        self._body: Callable[[MetaSession], None] = default_body_metabot
        self._fallback_body: Callable[[MetaSession], None] = default_fallback_body_metabot

    def set_bot_prediction(self, bot_prediction: Callable[[MetaSession, str], Bot]):
        bot_prediction_signature = inspect.signature(bot_prediction)
        bot_prediction_template_signature = inspect.signature(default_bot_prediction)
        if bot_prediction_signature.parameters != bot_prediction_template_signature.parameters:
            raise MetaBotPredictionSignatureError(self, bot_prediction, bot_prediction_template_signature, bot_prediction_signature)
        self._bot_prediction = bot_prediction

    def set_after_bot_prediction(self, after_bot_prediction: Callable[[MetaSession, str], Bot]):
        after_bot_prediction_signature = inspect.signature(after_bot_prediction)
        after_bot_prediction_template_signature = inspect.signature(default_after_bot_prediction)
        if after_bot_prediction_signature.parameters != after_bot_prediction_template_signature.parameters:
            raise MetaBotPredictionSignatureError(self, after_bot_prediction, after_bot_prediction_template_signature, after_bot_prediction_signature)
        self._bot_prediction = after_bot_prediction

    def set_body(self, body: Callable[[MetaSession], None]) -> None:
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_body_metabot)
        if body_signature.parameters != body_template_signature.parameters:
            raise MetaBotBodySignatureError(self, body, body_template_signature, body_signature)
        self._body = body

    def set_fallback_body(self, body: Callable[[MetaSession], None]) -> None:
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_fallback_body_metabot)
        if body_signature.parameters != body_template_signature.parameters:
            raise MetaBotBodySignatureError(self, body, body_template_signature, body_signature)
        self._fallback_body = body

    def add_bot(self, bot: Bot, description: str or None = None, free_states: list[State] or list[str] or None = None):
        if bot in self._bots:
            # TODO: Recursive addition of meta bots?
            raise Exception  # TODO: implement
        bot.description = description
        self._bots[bot.name] = bot
        if free_states is None:
            self._free_states[bot.name] = [state.name for state in bot.states]
        else:
            if all(isinstance(state, State) for state in free_states):
                free_states = [state.name for state in free_states]
            self._free_states[bot.name] = free_states

    def get_bot(self, name: str):
        if name in self._bots:
            return self._bots[name]
        else:
            return None

    def receive_message(self, session_id: str, message: str) -> None:
        redirect = False
        metabot_session: MetaSession = self.get_session(session_id)
        metabot_session.message = message
        target_bot = metabot_session._current_bot
        if target_bot is None:
            redirect = True
            target_bot = self.run_bot_prediction(metabot_session, message)
        if target_bot:
            metabot_session._current_bot = target_bot
            bot_session = target_bot.get_or_create_session(session_id, metabot_session.platform)
            if redirect:
                logging.info(f'[{self._name}] Redirecting to {target_bot.name}...')
                self.run_after_bot_prediction(metabot_session, bot_session)
            target_bot.receive_message(session_id, message)
            if bot_session.current_state.name in self._free_states[target_bot.name]:
                logging.info(f'[{target_bot.name}] Redirecting to {self._name}...')
                logging.info(f"[{self._name}] Running body {self._body.__name__}")
                self.run_body(metabot_session)
        else:
            logging.info(f"[{self._name}] Running fallback body {self._body.__name__}")
            self.run_fallback_body(metabot_session)

    def receive_file(self, session_id: str, file: File) -> None:
        pass

    def train(self):
        for _, bot in self._bots.items():
            # bot._sessions = self._sessions  # Assign the metabot's sessions object to all its bots
            bot.train()
        self._trained = True

    def _new_session(self, session_id: str, platform: Platform) -> Session:
        """Create a new session for the bot.

        Args:
            session_id (str): the session id
            platform (Platform): the platform where the session is to be created and used

        Returns:
            Session: the session
        """
        if session_id in self._sessions:
            # TODO: Raise exception
            pass
        if platform not in self._platforms:
            # TODO: Raise exception
            pass
        session = MetaSession(session_id, self, platform)
        self._sessions[session_id] = session
        self.run_body(session)
        return session

    def run_bot_prediction(self, session: MetaSession, message) -> Bot or None:
        try:
            return self._bot_prediction(session, message)
        except Exception as _:
            logging.error(f"An error occurred while predicting the bot in function '{self._bot_prediction.__name__}' of"
                          f"metabot '{self._name}'. See the attached exception:")
            traceback.print_exc()
            return None

    def run_after_bot_prediction(self, metabot_session: MetaSession, bot_session: Session) -> None:
        try:
            return self._after_bot_prediction(metabot_session, bot_session)
        except Exception as _:
            logging.error(f"An error occurred while running the 'after bot prediction' function"
                          f"'{self._after_bot_prediction.__name__}' of metabot '{self._name}'. See the attached"
                          f"exception:")
            traceback.print_exc()
            return None

    def run_body(self, session: MetaSession) -> None:
        try:
            self._body(session)
        except Exception as _:
            logging.error(f"An error occurred while executing body '{self._body.__name__}' of metabot '{self._name}'."
                          f"See the attached exception:")
            traceback.print_exc()

    def run_fallback_body(self, session: MetaSession) -> None:
        try:
            self._fallback_body(session)
        except Exception as _:
            logging.error(f"An error occurred while executing fallback body '{self._fallback_body.__name__}' of metabot"
                          f"'{self._name}'. See the attached exception:")
            traceback.print_exc()
