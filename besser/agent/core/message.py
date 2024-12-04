from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Enumeration of the different message types in :class:`Message`."""

    STR = 'str'
    MARKDOWN = 'markdown'
    HTML = 'html'
    FILE = 'file'
    IMAGE = 'image'
    DATAFRAME = 'dataframe'
    PLOTLY = 'plotly'
    LOCATION = 'location'
    OPTIONS = 'options'
    AUDIO = 'audio'
    RAG_ANSWER = 'rag_answer'


def get_message_type(value: str):
    for message_type in MessageType:
        if message_type.value == value:
            return message_type


class Message:
    """
    A conversation message. It is used by the streamlit UI to display the messages properly, depending on the sender
    (i.e., user or agent) and the type (string, audio, file, DataFrame, plot, etc.)

    Args:
        t (MessageType): The type of the message
        content (Any): The message content
        is_user (bool): Whether the message comes from the user (true) or the agent (false)
        timestamp (datetime): The timestamp of the message (when the message was sent)

    Attributes:
        type (MessageType): The type of the message
        content (Any): The message content
        is_user (bool): Whether the message comes from the user (true) or the agent (false)
        timestamp (datetime): The timestamp of the message (when the message was sent)
    """

    def __init__(self, t: MessageType, content: Any, is_user: bool, timestamp: datetime):
        self.type: MessageType = t
        self.content: Any = content
        self.is_user: bool = is_user
        self.timestamp: datetime = timestamp
        # TODO: Parse content to specific type (in DB, messages are stored a str)
