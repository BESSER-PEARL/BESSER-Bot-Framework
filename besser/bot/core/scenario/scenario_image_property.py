from besser.bot.core.image.image_property import ImageProperty
from besser.bot.core.scenario.scenario_element import ScenarioElement
from besser.bot.core.session import Session
from besser.bot.cv.prediction.image_prediction import ImagePropertyPrediction


class ScenarioImageProperty(ScenarioElement):

    def __init__(
            self,
            name: str,
            image_property: ImageProperty,
            score: float = 0,
    ):

        super().__init__(name)
        self.name: str = name
        self.image_property: ImageProperty = image_property
        self.score: float = score

    def evaluate(self, session: Session):
        if session.image_prediction is None:
            return False
        image_property_predictions: list[ImagePropertyPrediction] = session.image_prediction.image_property_predictions
        for image_property_prediction in image_property_predictions:
            if image_property_prediction.image_property == self.image_property and image_property_prediction.score >= self.score:
                return True
        return False
