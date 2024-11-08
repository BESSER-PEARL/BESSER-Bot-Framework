import base64
import json
import queue
from datetime import datetime

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from besser.bot.core.file import File
from besser.bot.core.message import MessageType, Message
from besser.bot.platforms.payload import PayloadEncoder, PayloadAction, Payload
from besser.bot.platforms.websocket.streamlit_ui.vars import WEBSOCKET, HISTORY, QUEUE, LAST_FILE, LAST_VOICE_MESSAGE


def sidebar():
    ws = st.session_state[WEBSOCKET]

    with st.sidebar:
        if reset_button := st.button(label="Reset bot"):
            st.session_state[HISTORY] = []
            st.session_state[QUEUE] = queue.Queue()
            payload = Payload(action=PayloadAction.RESET)
            ws.send(json.dumps(payload, cls=PayloadEncoder))

        if voice_bytes := audio_recorder(text=None, pause_threshold=2):
            if LAST_VOICE_MESSAGE not in st.session_state or st.session_state[LAST_VOICE_MESSAGE] != voice_bytes:
                st.session_state[LAST_VOICE_MESSAGE] = voice_bytes
                # Encode the audio bytes to a base64 string
                voice_message = Message(t=MessageType.AUDIO, content=voice_bytes, is_user=True, timestamp=datetime.now())
                st.session_state.history.append(voice_message)
                voice_base64 = base64.b64encode(voice_bytes).decode('utf-8')
                payload = Payload(action=PayloadAction.USER_VOICE, message=voice_base64)
                try:
                    ws.send(json.dumps(payload, cls=PayloadEncoder))
                except Exception as e:
                    st.error('Your message could not be sent. The connection is already closed')

        if uploaded_file := st.file_uploader("Choose a file", accept_multiple_files=False):
            if LAST_FILE not in st.session_state or st.session_state[LAST_FILE] != uploaded_file:
                st.session_state[LAST_FILE] = uploaded_file
                bytes_data = uploaded_file.read()
                file_object = File(file_base64=base64.b64encode(bytes_data).decode('utf-8'), file_name=uploaded_file.name,
                                   file_type=uploaded_file.type)
                payload = Payload(action=PayloadAction.USER_FILE, message=file_object.get_json_string())
                file_message = Message(t=MessageType.FILE, content=file_object.to_dict(), is_user=True,
                                       timestamp=datetime.now())
                st.session_state.history.append(file_message)
                try:
                    ws.send(json.dumps(payload, cls=PayloadEncoder))
                except Exception as e:
                    st.error('Your message could not be sent. The connection is already closed')
