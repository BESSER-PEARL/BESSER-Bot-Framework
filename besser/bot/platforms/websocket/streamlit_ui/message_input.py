import json
from datetime import datetime

import streamlit as st

from besser.bot.core.message import Message, MessageType
from besser.bot.platforms.payload import Payload, PayloadAction, PayloadEncoder
from besser.bot.platforms.websocket.streamlit_ui.vars import BUTTONS, SUBMIT_INPUT, WEBSOCKET, USER


def message_input():
    def submit_input():
        # Necessary callback due to buf after 1.27.0 (https://github.com/streamlit/streamlit/issues/7629)
        # It was fixed for rerun but with _handle_rerun_script_request it doesn't work
        st.session_state[SUBMIT_INPUT] = True

    user_input = st.chat_input("What is up?", on_submit=submit_input)
    if st.session_state[SUBMIT_INPUT]:
        st.session_state[SUBMIT_INPUT] = False
        if BUTTONS in st.session_state:
            del st.session_state[BUTTONS]
        with st.chat_message(USER):
            st.write(user_input)
        message = Message(t=MessageType.STR, content=user_input, is_user=True, timestamp=datetime.now())
        st.session_state.history.append(message)
        payload = Payload(action=PayloadAction.USER_MESSAGE,
                          message=user_input)
        try:
            ws = st.session_state[WEBSOCKET]
            ws.send(json.dumps(payload, cls=PayloadEncoder))
        except Exception as e:
            st.error('Your message could not be sent. The connection is already closed')