import base64

import cv2
import numpy as np
from openai import OpenAI

from besser.bot import nlp
from besser.bot.core.bot import Bot
from besser.bot.cv.vllm.vllm import VLLM


class VLLMOpenAI(VLLM):

    def __init__(self, bot: 'Bot', name: str, parameters: dict):
        super().__init__(bot.cv_engine, name, parameters)
        self.client: OpenAI = None

    def initialize(self) -> None:
        self.client = OpenAI(api_key=self._cv_engine._bot.get_property(nlp.OPENAI_API_KEY))

    def predict(self, message: str, img: np.ndarray, parameters: dict = None) -> str:
        retval, buffer = cv2.imencode('.jpg', img)  # Encode as JPEG
        base64_img = base64.b64encode(buffer).decode('utf-8')
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}",
                        "detail": "low"
                    },
                },
            ],
        }]
        if not parameters:
            parameters = self.parameters
        response = self.client.chat.completions.create(
            model=self.name,
            messages=messages,
            **parameters,
        )
        return response.choices[0].message.content
