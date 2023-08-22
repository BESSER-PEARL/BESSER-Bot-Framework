import logging


class Session:

    def __init__(self, session_id, bot, platform, current_state):
        self._id = session_id
        self._bot = bot
        self._platform = platform
        self._current_state = current_state
        self._dictionary = {}
        self._message = None
        self.predicted_intent = None
        self.chat_history: list[tuple[str, int]] = []

    @property
    def id(self):
        return self._id

    @property
    def platform(self):
        return self._platform

    @property
    def current_state(self):
        return self._current_state

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message: str):
        self.chat_history.append((message, 1))
        self._message = message

    def set(self, key, value):
        self._dictionary[key] = value

    def get(self, key):
        return self._dictionary[key]

    def delete(self, key):
        del self._dictionary[key]

    def move(self, transition):
        logging.info(transition.log())
        self._current_state = transition.dest
        self._current_state.run(self)

    def reply(self, message: str):
        # Multi-platform
        self._platform.reply(self, message)
