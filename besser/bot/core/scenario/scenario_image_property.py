from besser.bot.core.image.image_property import ImageProperty
from besser.bot.core.scenario.scenario_element import ScenarioElement
from besser.bot.core.session import Session


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
        # TODO: IMPLEMENT
        pass
