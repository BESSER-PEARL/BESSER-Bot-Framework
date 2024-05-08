class Message:
    """
    A conversation message. It is used by the streamlit UI to display the messages properly, depending on the sender
    (i.e., user or chatbot) and the type (string, audio, file, DataFrame, plot, etc.)

    Args:
        t (str): The type of the message
        content (Any): The message content
        is_user (bool): Whether the message comes from the user (true) or the chatbot (false)

    Attributes:
        type (str): The type of the message
        content (Any): The message content
        is_user (bool): Whether the message comes from the user (true) or the chatbot (false)
    """

    def __init__(self, t: str, content, is_user: bool):
        self.type: str = t
        self.content = content
        self.is_user: bool = is_user
