import json

from enum import Enum


class PayloadAction(Enum):
    """Enumeration of the different possible actions embedded into a :class:`Payload`."""

    USER_MESSAGE = 'user_message'
    """PayloadAction: Indicates that the payload's purpose is to send a user message."""

    USER_VOICE = 'user_voice'
    """PayloadAction: Indicates that the payload's purpose is to send a user audio."""
    
    USER_FILE = 'user_file'
    """PayloadAction: Indicates that the payload's purpose is to send a user file."""

    RESET = 'reset'
    """PayloadAction: Use the :class:`~besser.agent.platforms.websocket.websocket_platform.WebSocketPlatform` on this
    agent.
    """

    AGENT_REPLY_STR = 'agent_reply_str'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a :class:`str` object."""

    AGENT_REPLY_MARKDOWN = 'agent_reply_markdown'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a :class:`str` object
    in Markdown format."""

    AGENT_REPLY_HTML = 'agent_reply_html'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a :class:`str` object
    in HTML format."""

    AGENT_REPLY_FILE = 'agent_reply_file'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a :class:`file.File` 
    object."""
    
    AGENT_REPLY_IMAGE = 'agent_reply_image'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a :class:`file.File` 
    object, specifically an image."""

    AGENT_REPLY_DF = 'agent_reply_dataframe'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a :class:`pandas.DataFrame`
    object.
    """

    AGENT_REPLY_PLOTLY = 'agent_reply_plotly'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a 
    :class:`plotly.graph_objs.Figure` object.
    """

    AGENT_REPLY_OPTIONS = 'agent_reply_options'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a list of strings, where 
    the user should select 1 of them.
    """

    AGENT_REPLY_LOCATION = 'agent_reply_location'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a location, which is a
    dictionary composed by a latitude and a longitude.
    """

    AGENT_REPLY_RAG = 'agent_reply_rag'
    """PayloadAction: Indicates that the payload's purpose is to send an agent reply containing a RAG (Retrieval Augmented
    Generation) answer, which contains an LLM-generated answer and a set of documents the LLM used as context
    (see :class:`besser.agent.nlp.rag.rag.RAGMessage`).
    """


class Payload:
    """Represents a payload object used for encoding and decoding messages between an agent and any other external agent.
    """

    @staticmethod
    def decode(payload_str):
        """Decode a JSON payload string into a :class:`Payload` object.

        Args:
            payload_str (str or dict): A JSON-encoded payload string.

        Returns:
            Payload or None: A Payload object if the decoding is successful,
            None otherwise.
        """
        payload_dict = json.loads(payload_str)
        payload_action = payload_dict['action']
        payload_message = payload_dict['message']
        for action in PayloadAction:
            if action.value == payload_action:
                return Payload(action, payload_message)
        return None

    def __init__(self, action: PayloadAction, message: str or dict = None):
        self.action: str = action.value
        self.message: str or dict = message


class PayloadEncoder(json.JSONEncoder):
    """Encoder for the :class:`Payload` class.

    Example:
        .. code::

            import json
            encoded_payload = json.dumps(payload, cls=PayloadEncoder)
    """

    def default(self, obj):
        """Returns a serializable object for a :class:`Payload`

        Args:
            obj: the object to serialize

        Returns:
            dict: the serialized payload
        """
        if isinstance(obj, Payload):
            # Convert the Payload object to a dictionary
            payload_dict = {
                'action': obj.action,
                'message': obj.message,
            }
            return payload_dict
        return super().default(obj)
