from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.nlp.nlp_engine import NLPEngine


class Speech2Text(ABC):
    """The Speech2Text abstract class.

    The Speech2Text component, also known as STT, Automatic Speech Recognition or ASR, is in charge of converting spoken
    language or audio speech signals into written text. This task is called transcribing.

    We can use it in an agent to allow the users to send voice messages and transcribe them to written text so the agent
    can process them like regular text messages.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent

    Attributes:
        _nlp_engine (): The NLPEngine that handles the NLP processes of the agent
    """

    def __init__(self, nlp_engine: 'NLPEngine'):
        self._nlp_engine: 'NLPEngine' = nlp_engine

    @abstractmethod
    def speech2text(self, speech: bytes) -> str:
        """Transcribe a voice audio into its corresponding text representation.

        Args:
            speech (bytes): the recorded voice that wants to be transcribed

        Returns:
            str: the speech transcription
        """
        pass
