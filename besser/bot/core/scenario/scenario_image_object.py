from besser.bot.core.image.image_object import ImageObject
from besser.bot.core.scenario.scenario_element import ScenarioElement
from besser.bot.core.session import Session
from besser.bot.cv.prediction.image_prediction import ImageObjectPrediction


class ScenarioImageObject(ScenarioElement):

    def __init__(
            self,
            name: str,
            image_object: ImageObject,
            score: float = 0,
            min: int = 1,
            max: int = 0
    ):
        if min < 1:
            raise ValueError(f'Error creating {self.name}: min must be > 0')
        if min > max and max != 0:
            raise ValueError(f'Error creating {self.name}: min must <= max (unless max = 0)')
        super().__init__(name)
        self.name: str = name
        self.image_object: ImageObject = image_object
        self.min: int = min
        self.max: int = max
        self.score: float = score

    def evaluate(self, session: Session):
        if session.image_prediction is None:
            return False
        image_object_predictions: list[ImageObjectPrediction] = session.image_prediction.image_object_predictions
        filtered_image_object_predictions = [
            image_object_prediction for image_object_prediction in image_object_predictions
            if image_object_prediction.image_object == self.image_object and image_object_prediction.score >= self.score
        ]
        num_predictions = len(filtered_image_object_predictions)
        if num_predictions == 0:
            return False
        if self.min == 0 and self.max == 0:
            return True
        if self.min == 0 and num_predictions <= self.max:
            return True
        if self.max == 0 and num_predictions >= self.min:
            return True
        if self.min <= num_predictions <= self.max:
            return True
        return False
