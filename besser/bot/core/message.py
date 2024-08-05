from enum import Enum
from typing import Any


class MessageType(Enum):
    """Enumeration of the different message types in :class:`Message`."""

    STR = 'str'
    FILE = 'file'
    IMAGE = 'image'
    DATAFRAME = 'dataframe'
    PLOTLY = 'plotly'
    LOCATION = 'location'
    OPTIONS = 'options'
    AUDIO = 'audio'
    RAG_ANSWER = 'rag_answer'


class Message:
    """
    A conversation message. It is used by the streamlit UI to display the messages properly, depending on the sender
    (i.e., user or chatbot) and the type (string, audio, file, DataFrame, plot, etc.)

    Args:
        t (MessageType): The type of the message
        content (Any): The message content
        is_user (bool): Whether the message comes from the user (true) or the chatbot (false)

    Attributes:
        type (MessageType): The type of the message
        content (Any): The message content
        is_user (bool): Whether the message comes from the user (true) or the chatbot (false)
    """

    def __init__(self, t: MessageType, content: Any, is_user: bool):
        self.type: MessageType = t
        self.content: Any = content
        self.is_user: bool = is_user
