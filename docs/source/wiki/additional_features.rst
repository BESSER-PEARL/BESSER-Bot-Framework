Additional Features
===================

Here, you will find additional features that can be activated that are not part of the default features.


Speech-to-text
--------------
If the platform supports audio inputs from the user, a bot may accept audio input and will transcribe it to text. 
To enable audio processing, you need to set the fitting property (you can choose between using a Hugging Face model or the Google Spreech Recognition via the python `SpeechRecognition <https://github.com/Uberi/speech_recognition>`_ library):

.. code:: ini

    [nlp]
    # replace * with the desired model
    nlp.speech2text.hf.model = openai/whisper-*
    # OR
    nlp.speech2text.sr.engine = Google Speech Recognition

Note that for the Google Speech Recognition API, if a language was set, the API will also use the specified language when transcribing text.

