import datetime
from typing import Any, TYPE_CHECKING

import numpy as np

from besser.bot import cv
from besser.bot.core.property import Property
from besser.bot.cv.object_detection.object_detection_prediction import ObjectDetectionPrediction
from besser.bot.cv.object_detection.object_detector import ObjectDetector
from besser.bot.cv.vllm.vllm import VLLM

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class CVEngine:
    """The CV Engine of a bot.

    It is in charge of running different Computer Vision tasks required by the bot.

    Args:
        bot (Bot): the bot the CVEngine belongs to

    Attributes:
        _bot (Bot): The bot the CVEngine belongs to
        _object_detectors (list[ObjectDetector]): Object Detection Systems of the CVEngine
        _vllms (dict[str, VLLM]): The VLLMs of the CVEngine. Keys are the names and values are the VLLMs themselves.
    """

    def __init__(self, bot: 'Bot'):
        self._bot: 'Bot' = bot
        self._object_detectors: list[ObjectDetector] = []
        self._vllms: dict[str, VLLM] = {}

    @property
    def object_detectors(self):
        """list[ObjectDetector]: The Object Detector of the CVEngine"""
        return self._object_detectors

    @property
    def vllms(self):
        """dict[str, VLLM]: The VLLMs of the CVEngine"""
        return self._vllms

    def initialize(self) -> None:
        """Initialize the CVEngine."""
        for object_detector in self._object_detectors:
            object_detector.initialize()
        for vllm_name, vllm in self._vllms.items():
            vllm.initialize()

    def get_property(self, prop: Property) -> Any:
        """Get a CV property's value from the CVEngine's bot.

        Args:
            prop (Property): the property to get its value

        Returns:
            Any: the property value, or None if the property is not a CV property
        """
        if prop.section != cv.SECTION_CV:
            return None
        return self._bot.get_property(prop)

    def train(self) -> None:
        """Train the CV components of the CVEngine."""
        for object_detector in self._object_detectors:
            object_detector.train()

    def detect_objects(self, img: np.ndarray) -> ObjectDetectionPrediction:
        """Detect objects from an image.

        Args:
            img (np.ndarray): the image to detect objects from

        Returns:
            ObjectDetectionPrediction: the object detection prediction
        """
        prediction = ObjectDetectionPrediction(
            img=img,
            image_object_predictions=[],
            timestamp=datetime.datetime.now(),
            image_input_name=None  # TODO: For now, this is ignored
        )
        for object_detector in self._object_detectors:
            prediction.image_object_predictions.extend(object_detector.predict(img))
        return prediction
