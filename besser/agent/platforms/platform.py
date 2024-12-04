from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from besser.agent.platforms.payload import Payload

if TYPE_CHECKING:
    from besser.agent.core.session import Session


class Platform(ABC):
    """The platform abstract class.

    A platform defines the methods the agent can use to interact with a particular communication channel
    (e.g. Telegram, Slack...) for instance, sending and receiving messages.

    This class serves as a template to implement platforms.

    Attributes:
        running (bool): Whether the platform is running or not
    """

    def __init__(self):
        self.running = False

    def run(self) -> None:
        """Run the platform."""
        self.initialize()
        self.start()

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the platform. This function is called right before starting the platform."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the platform."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Terminate the platform execution."""
        pass

    @abstractmethod
    def _send(self, session_id: str, payload: Payload) -> None:
        """Send a payload message to a specific user.

        Args:
            session_id (str): the user to send the response to
            payload (Payload): the payload message to send to the user
        """
        pass

    @abstractmethod
    def reply(self, session: 'Session', message: str) -> None:
        """Send an agent reply, i.e. a text message, to a specific user.

        Args:
            session (Session): the user session
            message (str): the message to send to the user
        """
        pass
