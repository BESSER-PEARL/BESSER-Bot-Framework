import datetime
import json

import numpy as np

from besser.bot.core.image.image_object import ImageObject


class ImageObjectPrediction:
    """The prediction result of an ObjectDetector for a specific ImageObject.

    Args:
        image_object (ImageObject):
        score (float): the prediction score (between 0 and 1)
        x1 (int): the x1 coordinate of the object's bounding box
        y1 (int): the y1 coordinate of the object's bounding box
        x2 (int): the x2 coordinate of the object's bounding box
        y2 (int): the y2 coordinate of the object's bounding box

    Attributes:
        image_object (ImageObject):
        score (float): the prediction score (between 0 and 1)
        x1 (int): the x1 coordinate of the object's bounding box
        y1 (int): the y1 coordinate of the object's bounding box
        x2 (int): the x2 coordinate of the object's bounding box
        y2 (int): the y2 coordinate of the object's bounding box
    """

    def __init__(self, image_object: ImageObject, score: float, x1: int, y1: int, x2: int, y2: int):
        self.image_object: ImageObject = image_object
        self.score: float = score
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2


class ObjectDetectionPrediction:
    """The prediction result of an ObjectDetector for a specific image.

    Args:
        img (np.ndarray): the image on which the object detection was done
        image_object_predictions (list[ImageObjectPrediction]): the list of predicted objects within the image
        timestamp (datetime.datetime): the time at which the prediction was done
        model_name (str): the name of the model that made the object detection
        image_input_name (str): the name of the image input source

    Attributes:
        img (np.ndarray): the image on which the object detection was done
        image_object_predictions (list[ImageObjectPrediction]): the list of predicted objects within the image
        timestamp (datetime.datetime): the time at which the prediction was done
        model_name (str): the name of the model that made the object detection
        image_input_name (str): the name of the image input source
    """
    def __init__(
            self,
            img: np.ndarray,
            image_object_predictions: list[ImageObjectPrediction],
            timestamp: datetime.datetime,
            model_name: str,
            image_input_name: str

    ):
        self.img: np.ndarray = img
        self.image_object_predictions: list[ImageObjectPrediction] = image_object_predictions
        self.timestamp: datetime.datetime = timestamp
        self.model_name: str = model_name
        self.image_input_name: str = image_input_name

    def get_image_object_predictions(self, name: str) -> list[ImageObjectPrediction]:
        """Get all the image object predictions with a specific image object name.

        Args:
            name (str): the name of the image objects to get

        Returns:
            list[ImageObjectPrediction]: the image object predictions whose image object's name matches with the
            provided name
        """
        image_object_predictions: list[ImageObjectPrediction] = []
        for image_object_prediction in self.image_object_predictions:
            if image_object_prediction.image_object.name == name:
                image_object_predictions.append(image_object_prediction)
        return image_object_predictions


class ObjectDetectionPredictionEncoder(json.JSONEncoder):
    """Encoder for the :class:`ObjectDetectionPrediction` class.

    Example:
        .. code::

            import json
            encoded_object_detection_prediction = json.dumps(object_detection_prediction, cls=ObjectDetectionPredictionEncoder)
    """

    def default(self, obj):
        """Returns a serializable object for a :class:`ObjectDetectionPrediction`

        Args:
            obj: the object to serialize

        Returns:
            dict: the serialized object detection prediction
        """
        if isinstance(obj, ObjectDetectionPrediction):
            # Convert the ObjectDetectionPrediction object to a dictionary
            object_detection_prediction_dict = {
                # 'img': obj.img.tolist(),
                'image_object_predictions': []
            }
            for image_object_prediction in obj.image_object_predictions:
                object_detection_prediction_dict['image_object_predictions'].append({
                    'name': image_object_prediction.image_object.name,
                    'score': image_object_prediction.score,
                    'x1': image_object_prediction.x1,
                    'x2': image_object_prediction.x2,
                    'y1': image_object_prediction.y1,
                    'y2': image_object_prediction.y2,
                })
            return object_detection_prediction_dict
        return super().default(obj)
