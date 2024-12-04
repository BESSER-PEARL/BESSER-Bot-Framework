import base64
import json


class File:
    """A representation of files sent and received by an agent.

    Files are used to encapsulate information about the files exchanged in an agent conversation. They include
    attributes such as the file's name, type, and base64 representation.
    Note that at least one of path, data or base64 need to be set. 

    Args:
        file_name (str): The name of the file.
        file_type (str): The type of the file.
        file_base64 (str, optional): The base64 representation of the file.
        file_path (str, optional): Path to the file.
        file_data (bytes, optional): Raw file data.

    Attributes:
        _name (str): The name of the file.
        _type (str): The type of the file.
        _base64 (str): The base64 representation of the file.
    """

    def __init__(self, file_name: str = None, file_type: str = None, file_base64: str = None, file_path: str = None, file_data: bytes = None):
        if file_path:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_name = file_path.split('/')[-1]
                file_type = file_path.split('.')[-1]
        elif file_base64:
            file_data = base64.b64decode(file_base64)
        elif file_data is None:
            raise ValueError("Invalid input parameters")
        if not file_name:
            file_name = 'default_filename'
        if not file_type:
            file_type = 'file'
        self._name = file_name
        self._type = file_type
        self._base64 = base64.b64encode(file_data).decode('utf-8')

    @property
    def name(self) -> str:
        """Getter for the name of the file."""
        return self._name

    @property
    def type(self) -> str:
        """Getter for the type of the file."""
        return self._type

    @property
    def base64(self) -> str:
        """Getter for the base64 representation of the file."""
        return self._base64

    @name.setter
    def name(self, value: str) -> None:
        """Setter for the name of the file."""
        self._name = value

    @type.setter
    def type(self, value: str) -> None:
        """Setter for the type of the file."""
        self._type = value

    @base64.setter
    def base64(self, value: str) -> None:
        """Setter for the base64 representation of the file."""
        self._base64 = value

    @staticmethod
    def decode(file_str):
        """Decode a JSON payload string into a :class:`File` object.

        Args:
            file_str (str): A JSON-encoded file string.

        Returns:
            File or None: A File object if the decoding is successful,
            None otherwise.
        """
        file_dict = json.loads(file_str)
        file_name = file_dict['name']
        file_type = file_dict['type']
        file_base64 = file_dict['base64']
        if file_name and file_type and file_base64:
            return File(file_name=file_name, file_type=file_type, file_base64=file_base64)
        return None
    
    def get_json_string(self) -> str:
        """Returns a stringified dictionary containing the attributes of the File object."""
        return json.dumps({
            "name": self.name,
            "type": self.type,
            "base64": self.base64,
        })

    def to_dict(self):
        """Returns a dictionary containing the attributes of the File object."""
        return {
            "name": self.name,
            "type": self.type,
            "base64": self.base64,
        }
        
    @staticmethod
    def from_dict(data):
        """Returns a File object generated based on the given dict object."""
        return File(file_base64=data['base64'], file_type=data['type'], file_name=data['name'])
