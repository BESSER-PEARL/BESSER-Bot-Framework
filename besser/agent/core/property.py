from typing import Any


class Property:
    """An agent property.

    Args:
        section (str): the property section
        name (str): the property name
        property_type (type): the property type
        default_value (Any): the property default value

    Attributes:
        section (str): The property section
        name (str): The property name
        type (type): The property type
        default_value (Any): The property default value
    """
    def __init__(self, section: str, name: str, property_type: type, default_value: Any):
        if (default_value is not None) and (not isinstance(default_value, property_type)):
            raise TypeError(f"Attempting to create a property '{name}' in section '{section}' with a "
                            f"{type(default_value)} default value: {default_value}. The expected property value type "
                            f"is {property_type}")
        self.section = section
        self.name = name
        self.type = property_type
        self.default_value = default_value
