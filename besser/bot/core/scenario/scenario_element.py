from abc import ABC, abstractmethod

from besser.bot.core.session import Session


class ScenarioElement(ABC):

    def __init__(self, name: str):
        self.name: str = name

    def __str__(self):
        return self.name

    @abstractmethod
    def evaluate(self, session: Session):
        pass
