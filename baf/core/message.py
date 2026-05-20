from datetime import datetime
from enum import Enum
from typing import Any

from baf.platforms.payload import PayloadAction


class MessageType(Enum):
    """Enumeration of the different message types in :class:`Message`."""

    STR = 'str'
    JSON = 'json'
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
    UI = 'ui'
    REASONING_TRACE = 'reasoning_trace'  # UI-internal synthetic type aggregating streamed reasoning_step / task_list_update events


def get_message_type(value: str):
    for message_type in MessageType:
        if message_type.value == value:
            return message_type
    return None


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

    def get_action(self):
        if self.is_user:
            match self.type:
                case MessageType.STR:
                    return PayloadAction.USER_MESSAGE
                case MessageType.JSON:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.MARKDOWN:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.HTML:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.FILE:
                    return PayloadAction.USER_FILE
                case MessageType.IMAGE:
                    return PayloadAction.USER_FILE  # TODO: Not implemented
                case MessageType.DATAFRAME:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.PLOTLY:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.LOCATION:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.OPTIONS:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.AUDIO:
                    return PayloadAction.USER_VOICE
                case MessageType.RAG_ANSWER:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
                case MessageType.UI:
                    return PayloadAction.USER_MESSAGE  # TODO: Not implemented
        else:
            match self.type:
                case MessageType.STR:
                    return PayloadAction.AGENT_REPLY_STR
                case MessageType.JSON:
                    return PayloadAction.AGENT_REPLY_STR  # TODO: Not implemented
                case MessageType.MARKDOWN:
                    return PayloadAction.AGENT_REPLY_MARKDOWN
                case MessageType.HTML:
                    return PayloadAction.AGENT_REPLY_HTML
                case MessageType.FILE:
                    return PayloadAction.AGENT_REPLY_FILE
                case MessageType.IMAGE:
                    return PayloadAction.AGENT_REPLY_IMAGE
                case MessageType.DATAFRAME:
                    return PayloadAction.AGENT_REPLY_DF
                case MessageType.PLOTLY:
                    return PayloadAction.AGENT_REPLY_PLOTLY
                case MessageType.LOCATION:
                    return PayloadAction.AGENT_REPLY_LOCATION
                case MessageType.OPTIONS:
                    return PayloadAction.AGENT_REPLY_OPTIONS
                case MessageType.AUDIO:
                    return PayloadAction.AGENT_REPLY_AUDIO
                case MessageType.RAG_ANSWER:
                    return PayloadAction.AGENT_REPLY_RAG
                case MessageType.UI:
                    return PayloadAction.AGENT_REPLY_UI
