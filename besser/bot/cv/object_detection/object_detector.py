from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

from besser.bot.cv.prediction.image_prediction import ImageObjectPrediction

if TYPE_CHECKING:
    from besser.bot.cv.cv_engine import CVEngine


class ObjectDetector(ABC):
    """The Object Detector abstract class.

    An Object Detector receives an image as input and detects multiple objects within the image.

    Args:
        cv_engine (CVEngine): the CVEngine that handles the CV processes of the bot the Object Detector belongs to
        name (str): the Object Detector name
        parameters (dict): the Object Detector parameters

    Attributes:
        _cv_engine (CVEngine): the CVEngine that handles the CV processes of the bot the Object Detector belongs to
        name (str): the Object Detector name
        parameters (dict): the Object Detector parameters
    """

    def __init__(self, cv_engine: 'CVEngine', name: str, parameters: dict):
        self._cv_engine: 'CVEngine' = cv_engine
        self.name: str = name
        self.parameters: dict = parameters
        self._cv_engine.object_detectors.append(self)

    def set_parameters(self, parameters: dict) -> None:
        """Set the Object Detector parameters.

        Args:
            parameters (dict): the new Object Detector parameters
        """
        self.parameters = parameters

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the Object Detector. This function is called during the bot training."""
        pass

    @abstractmethod
    def train(self) -> None:
        """Train the Object Detector. This function is called during the bot training."""
        pass

    @abstractmethod
    def predict(self, img: np.ndarray) -> list[ImageObjectPrediction]:
        """Detect objects from an image.

        Args:
            img (np.ndarray): the image to detect objects from

        Returns:
            list[ImageObjectPrediction]: the image object predictions
        """
        pass
