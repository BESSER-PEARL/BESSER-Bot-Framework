from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from besser.bot.cv.cv_engine import CVEngine


class VLLM(ABC):

    def __init__(self, cv_engine: 'CVEngine', name: str, parameters: dict):
        self._cv_engine: 'CVEngine' = cv_engine
        self.name: str = name
        self.parameters: dict = parameters
        self._cv_engine.vllms[name] = self
        # TODO: Global/user context like in LLM?

    def set_parameters(self, parameters: dict) -> None:
        """Set the VLLM parameters.

        Args:
            parameters (dict): the new VLLM parameters
        """
        self.parameters = parameters

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the VLLM. This function is called during the bot training."""
        pass

    @abstractmethod
    def predict(self, message: str, img: np.ndarray, parameters: dict = None) -> str:
        """Make a prediction, i.e., generate an output.

        Args:
            message (Any): the VLLM input text
            img (np.ndarray): the vllm input image
            parameters (dict): the VLLM parameters to use in the prediction. If none is provided, the default VLLM
                parameters will be used

        Returns:
            str: the LLM output
        """
        pass
