Speech-to-Text
==============

BBF allows you to use your voice to interact with the agents, transforming them into voicebots! To do this, it
implements a Speech-to-Text component (also known as automatic speech recognition, STT or S2T). It solves the NLP task
of transcribing an audio file. Then, the transcription is treated as a typical user text message.

Currently BBF has 2 different implementations for speech-to-text:

- With HuggingFace models (only tested with openai/whisper models). You need to set the
  :obj:`~besser.agent.nlp.NLP_STT_HF_MODEL` agent property. Example model: ``openai/whisper-tiny`` (very lightweight model)

- With the `SpeechRecognition <https://github.com/Uberi/speech_recognition>`_ Python library. You need to set the
  :obj:`~besser.agent.nlp.NLP_STT_SR_ENGINE` agent property.
