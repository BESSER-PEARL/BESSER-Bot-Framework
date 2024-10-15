import datetime
import math
from typing import TYPE_CHECKING

import numpy as np
from ultralytics import YOLO
from ultralytics.engine.results import Results

from besser.bot.core.image.image_object import ImageObject
from besser.bot.cv.object_detection.object_detection_prediction import ImageObjectPrediction, ObjectDetectionPrediction
from besser.bot.cv.object_detection.object_detector import ObjectDetector

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class_names = [
    "person",
    "bicycle",
    "car",
    "motorbike",
    "aeroplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "sofa",
    "pottedplant",
    "bed",
    "diningtable",
    "toilet",
    "tvmonitor",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush"
]


class YOLOObjectDetector(ObjectDetector):
    """The YOLO Object Detector.

    Args:
        bot (Bot): the bot the Object Detector belongs to
        name (str): the Object Detector name
        parameters (dict): the Object Detector parameters

    Attributes:
        _cv_engine (CVEngine): the CVEngine that handles the CV processes of the bot the Object Detector belongs to
        name (str): the Object Detector name
        parameters (dict): the Object Detector parameters
        yolo (YOLO): the YOLO object detection model
    """

    def __init__(self, bot: 'Bot', name: str, model_path: str, parameters: dict = {}):
        super().__init__(bot.cv_engine, name, parameters)
        self.yolo: YOLO = YOLO(model_path)

    def initialize(self) -> None:
        pass

    def train(self) -> None:
        pass

    def predict(self, img: np.ndarray) -> ObjectDetectionPrediction:
        timestamp = datetime.datetime.now()
        results: list[Results] = self.yolo(img, stream=False)
        image_object_predictions: list[ImageObjectPrediction] = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                score = math.ceil((box.conf[0] * 100)) / 100
                cls = box.cls[0]
                name = class_names[int(cls)]
                image_object: ImageObject = self._cv_engine._bot.get_image_object(name)
                if image_object:
                    image_object_prediction: ImageObjectPrediction = ImageObjectPrediction(
                        image_object=image_object,
                        score=score,
                        x1=x1, y1=y1, x2=x2, y2=y2
                    )
                    image_object_predictions.append(image_object_prediction)

        object_detection_prediction: ObjectDetectionPrediction = ObjectDetectionPrediction(
            img=img,
            image_object_predictions=image_object_predictions,
            timestamp=timestamp,
            model_name=self.name,
            image_input_name='CAMERA'  # TODO: For now, this is ignored
        )
        return object_detection_prediction
