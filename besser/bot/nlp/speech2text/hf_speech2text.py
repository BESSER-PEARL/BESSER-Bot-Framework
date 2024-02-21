import io
from typing import TYPE_CHECKING

import librosa
from transformers import AutoProcessor, TFAutoModelForSpeechSeq2Seq, logging

from besser.bot import nlp
from besser.bot.nlp.speech2text.speech2text import Speech2Text

if TYPE_CHECKING:
    from besser.bot.nlp.nlp_engine import NLPEngine

logging.set_verbosity_error()


class HFSpeech2Text(Speech2Text):
    """A Hugging Face Speech2Text.

    It loads a Speech2Text Hugging Face model to perform the Speech2Text task.

    .. warning::

        Only tested with ``openai/whisper-*`` models

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot

    Attributes:
        _model_name (str): the Hugging Face model name
        _processor (): the model text processor
        _model (): the Speech2Text model
        _sampling_rate (int): the sampling rate of audio data, it must coincide with the sampling rate used to train the
            model
        _forced_decoder_ids (list): the decoder ids
    """

    def __init__(self, nlp_engine: 'NLPEngine'):
        super().__init__(nlp_engine)
        # TODO: USE PIPELINE TO ALLOW ALL STT MODELS
        # https://huggingface.co/docs/transformers/pipeline_tutorial
        self._model_name: str = self._nlp_engine.get_property(nlp.NLP_STT_HF_MODEL)
        self._processor = AutoProcessor.from_pretrained(self._model_name)
        self._model = TFAutoModelForSpeechSeq2Seq.from_pretrained(self._model_name)
        self._sampling_rate: int = 16000
        # self.model.config.forced_decoder_ids = None
        self._forced_decoder_ids = self._processor.get_decoder_prompt_ids(
            language=self._nlp_engine.get_property(nlp.NLP_LANGUAGE), task="transcribe"
        )

    def speech2text(self, speech: bytes):
        wav_stream = io.BytesIO(speech)
        audio, sampling_rate = librosa.load(wav_stream, sr=self._sampling_rate)
        input_features = self._processor(audio, sampling_rate=self._sampling_rate, return_tensors="tf").input_features
        predicted_ids = self._model.generate(input_features, forced_decoder_ids=self._forced_decoder_ids)
        transcriptions = self._processor.batch_decode(predicted_ids, skip_special_tokens=True)
        return transcriptions[0]
