import json
import queue
import sys
import threading
import time
import pandas as pd
import streamlit as st
import websocket

from streamlit.runtime import Runtime
from streamlit.runtime.app_session import AppSession
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.web import cli as stcli

from besser.bot.server.Payload import Payload, PayloadEncoder


def main():

    def on_message(ws, payload_str):
        # https://github.com/streamlit/streamlit/issues/2838
        streamlit_session = get_streamlit_session(get_browser_session_id())
        payload: Payload = Payload.decode(payload_str)
        if payload.action == Payload.BOT_REPLY_STR:
            message = payload.message
        elif payload.action == Payload.BOT_REPLY_DF:
            message = pd.read_json(payload.message)

        streamlit_session._session_state['queue'].put(message)
        streamlit_session._handle_rerun_script_request()

    def on_error(ws, error):
        print(f'({ws.id}):', error)

    def on_open(ws):
        pass

    def on_close(ws, close_status_code, close_msg):
        print(f'({ws.id}) closed with status code {close_status_code} and close message: {close_msg}')

    st.set_page_config(
        page_title="Streamlit Chat - Demo",
        page_icon=":robot:"
    )

    user_type = {
        0: 'assistant',
        1: 'user'
    }

    st.header("Chat Demo")
    st.markdown("[Github](https://github.com/BESSER-PEARL/bot-framework)")

    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'queue' not in st.session_state:
        st.session_state['queue'] = queue.Queue()

    if 'websocket' not in st.session_state:
        ws = websocket.WebSocketApp(f"ws://localhost:8765/",
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        server_thread = threading.Thread(target=ws.run_forever)
        add_script_run_ctx(server_thread)
        server_thread.start()
        st.session_state['websocket'] = ws

    ws = st.session_state['websocket']

    with st.sidebar:
        with st.form(key="resetForm"):
            reset_button = st.form_submit_button(label="Reset bot")
            if reset_button:
                st.session_state['history'] = []
                st.session_state['queue'] = queue.Queue()
                payload = Payload(action=Payload.RESET)
                ws.send(json.dumps(payload, cls=PayloadEncoder))

    for message in st.session_state['history']:
        with st.chat_message(user_type[message[1]]):
            st.write(message[0])

    while not st.session_state['queue'].empty():
        message = st.session_state['queue'].get()
        st.session_state['history'].append((message, 0))
        with st.chat_message("assistant"):
            if isinstance(message, str):
                message_placeholder = st.empty()
                full_response = ""
                # Simulate stream of response with milliseconds delay
                for chunk in message.split():
                    full_response += chunk + " "
                    time.sleep(0.04)
                    # Add a blinking cursor to simulate typing
                    message_placeholder.write(full_response + "▌")
                message_placeholder.write(full_response)
            else:
                st.write(message)

    # React to user input
    if user_input := st.chat_input("What is up?"):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.history.append((user_input, 1))
        payload = Payload(action=Payload.USER_MESSAGE,
                          message=user_input)
        ws.send(json.dumps(payload, cls=PayloadEncoder))


def get_browser_session_id() -> str:
    # Get the session_id for the current running script
    try:
        ctx = get_script_run_ctx()
        return ctx.session_id
    except Exception as e:
        raise Exception("Could not get browser session id") from e


def get_streamlit_session(session_id: str) -> AppSession:
    runtime: Runtime = Runtime.instance()
    session = next((
        s.session
        for s in runtime._session_mgr.list_sessions()
        if s.session.id == session_id
    ), None)
    if session is None:
        raise Exception(f"Streamlit session not found for {session_id}")
    return session


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
