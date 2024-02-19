import io
import logging
from typing import TYPE_CHECKING

import speech_recognition as sr

from besser.bot import nlp
from besser.bot.nlp.speech2text.speech2text import Speech2Text
from besser.bot.exceptions.exceptions import SREngineNotFound
if TYPE_CHECKING:
    from besser.bot.nlp.nlp_engine import NLPEngine

# TODO: Once implemented, add the other engines here
engines = ["Google Speech Recognition"]


class APISpeech2Text(Speech2Text):
    """Makes use of the python speech_recognition library.

    The library calls to different speech recognition engines/APIs.

    Currently, supports:
        Google Speech Recognition

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot

    Attributes:
        _sr_engine (str): the chosen SR engine
        _language (str): the chosen language
    """

    def __init__(self, nlp_engine: 'NLPEngine'):
        super().__init__(nlp_engine)
        if self._nlp_engine.get_property(nlp.NLP_STT_SR_ENGINE) not in engines:
            raise SREngineNotFound(self._nlp_engine.get_property(nlp.NLP_STT_SR_ENGINE), engines)
        self._sr_engine = self._nlp_engine.get_property(nlp.NLP_STT_SR_ENGINE)
        self._language = self._nlp_engine.get_property(nlp.NLP_LANGUAGE)

    def speech2text(self, speech: bytes):
        wav_stream = io.BytesIO(speech)
        r = sr.Recognizer()
        text = ""
        # Record the audio data from the stream
        with sr.AudioFile(wav_stream) as source:
            audio_data = r.record(source)
            try:
                # Recognize the audio data
                # add other platforms here
                if self._sr_engine == "Google Speech Recognition":
                    if self._language is None:
                        # use english per default
                        text = r.recognize_google(audio_data)
                    else:
                        text = r.recognize_google(audio_data, language=self._language)
                
            except Exception as e:
                # Currently throws an error when starting the bot
                # Or when trying to create an audio file on firefox
                logging.error('Empty audio file"')
        return text
