import queue
import sys
import threading

import streamlit as st
import websocket
from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx

from besser.agent.platforms.websocket.streamlit_ui.session_management import session_monitoring
from besser.agent.platforms.websocket.streamlit_ui.vars import SESSION_MONITORING_INTERVAL, SUBMIT_TEXT, HISTORY, QUEUE, \
    WEBSOCKET, SESSION_MONITORING, SUBMIT_AUDIO, SUBMIT_FILE
from besser.agent.platforms.websocket.streamlit_ui.websocket_callbacks import on_open, on_error, on_message, on_close, on_ping, on_pong


def initialize():
    if SUBMIT_TEXT not in st.session_state:
        st.session_state[SUBMIT_TEXT] = False

    if SUBMIT_AUDIO not in st.session_state:
        st.session_state[SUBMIT_AUDIO] = False

    if SUBMIT_FILE not in st.session_state:
        st.session_state[SUBMIT_FILE] = False

    if HISTORY not in st.session_state:
        st.session_state[HISTORY] = []

    if QUEUE not in st.session_state:
        st.session_state[QUEUE] = queue.Queue()

    if WEBSOCKET not in st.session_state:
        try:
            # We get the websocket host and port from the script arguments
            host = sys.argv[2]
            port = sys.argv[3]
        except Exception as e:
            # If they are not provided, we use default values
            host = 'localhost'
            port = '8765'
        ws = websocket.WebSocketApp(f"ws://{host}:{port}/",
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    on_ping=on_ping,
                                    on_pong=on_pong)
        websocket_thread = threading.Thread(target=ws.run_forever)
        add_script_run_ctx(websocket_thread)
        websocket_thread.start()
        st.session_state[WEBSOCKET] = ws

    if SESSION_MONITORING not in st.session_state:
        session_monitoring_thread = threading.Thread(target=session_monitoring,
                                                     kwargs={'interval': SESSION_MONITORING_INTERVAL})
        add_script_run_ctx(session_monitoring_thread)
        session_monitoring_thread.start()
        st.session_state[SESSION_MONITORING] = session_monitoring_thread
