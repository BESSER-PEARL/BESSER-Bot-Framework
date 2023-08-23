from abc import ABC, abstractmethod


class Platform(ABC):

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def _send(self, session_id, payload):
        pass

    @abstractmethod
    def reply(self, session, message):
        pass
