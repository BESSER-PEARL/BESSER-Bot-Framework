class ImageObject:
    """The Image Object core component of a bot.

    Image Objects are used to specify the elements that can be detected by the bot in an image.

    Args:
        name (str): the image object's name
        description (str or None): a description of the image object, optional

    Attributes:
        name (str): The image object's name
        description (str or None): A description of the image object, optional
    """

    def __init__(self, name: str, description: str = None):
        self.name: str = name
        self.description: str = description

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)
