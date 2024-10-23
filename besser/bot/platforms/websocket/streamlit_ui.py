import base64
import json
import queue
import sys
import threading
import time
from datetime import datetime

import cv2
import pandas as pd
import plotly
import streamlit as st
import websocket
from audio_recorder_streamlit import audio_recorder
from streamlit.runtime import Runtime
from streamlit.runtime.app_session import AppSession
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.web import cli as stcli

from besser.bot.core.file import File
from besser.bot.core.message import Message, MessageType
from besser.bot.platforms.payload import Payload, PayloadAction, PayloadEncoder

# Time interval to check if a streamlit session is still active, in seconds
SESSION_MONITORING_INTERVAL = 1
# To enable/disable video input (images from camera input sent to the bot)
# TODO: Temporary solution
VIDEO_INPUT_ENABLED = False
# Time interval to send images to the bot
VIDEO_INPUT_INTERVAL = 0.2


def get_streamlit_session() -> AppSession or None:
    session_id = get_script_run_ctx().session_id
    runtime: Runtime = Runtime.instance()
    return next((
        s.session
        for s in runtime._session_mgr.list_sessions()
        if s.session.id == session_id
    ), None)


def session_monitoring(interval: int):
    runtime: Runtime = Runtime.instance()
    session = get_streamlit_session()
    while True:
        time.sleep(interval)
        if not runtime.is_active_session(session.id):
            runtime.close_session(session.id)
            session.session_state['websocket'].close()
            break


def video_input():
    """This function periodically sends images to the bot at a specific frequency (defined by VIDEO_INPUT_INTERVAL, in
    seconds)"""
    # TODO: FINISH WHEN SESSION IS CLOSED
    session = get_streamlit_session()
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    while True:
        if 'img' not in session._session_state:
            ws = session._session_state['websocket']
            success, img = cap.read()
            if success:
                session.session_state['img'] = img
                retval, buffer = cv2.imencode('.jpg', img)  # Encode as JPEG
                base64_img = base64.b64encode(buffer).decode('utf-8')
                payload = Payload(action=PayloadAction.USER_IMAGE,
                                  message=base64_img)
                try:
                    ws.send(json.dumps(payload, cls=PayloadEncoder))
                except Exception as e:
                    print('Your message (image from video input) could not be sent. The connection is already closed')
                    break
        time.sleep(VIDEO_INPUT_INTERVAL)


def main():
    try:
        # We get the websocket host and port from the script arguments
        bot_name = sys.argv[1]
    except Exception as e:
        # If they are not provided, we use default values
        bot_name = 'Chatbot Demo'
    st.header(bot_name)
    st.markdown("[Github](https://github.com/BESSER-PEARL/BESSER-Bot-Framework)")
    # User input component. Must be declared before history writing
    user_input = st.chat_input("What is up?")

    def on_message(ws, payload_str):
        # https://github.com/streamlit/streamlit/issues/2838
        streamlit_session = get_streamlit_session()
        payload: Payload = Payload.decode(payload_str)
        if payload.action == PayloadAction.BOT_REPLY_STR.value:
            content = payload.message
            t = MessageType.STR
        elif payload.action == PayloadAction.BOT_REPLY_FILE.value:
            content = payload.message
            t = MessageType.FILE
        elif payload.action == PayloadAction.BOT_REPLY_DF.value:
            content = pd.read_json(payload.message)
            t = MessageType.DATAFRAME
        elif payload.action == PayloadAction.BOT_REPLY_PLOTLY.value:
            content = plotly.io.from_json(payload.message)
            t = MessageType.PLOTLY
        elif payload.action == PayloadAction.BOT_REPLY_LOCATION.value:
            content = {
                'latitude': [payload.message['latitude']],
                'longitude': [payload.message['longitude']]
            }
            t = MessageType.LOCATION
        elif payload.action == PayloadAction.BOT_REPLY_OPTIONS.value:
            t = MessageType.OPTIONS
            d = json.loads(payload.message)
            content = []
            for button in d.values():
                content.append(button)
        elif payload.action == PayloadAction.BOT_REPLY_RAG.value:
            t = MessageType.RAG_ANSWER
            content = payload.message
        elif payload.action == PayloadAction.BOT_REPLY_OBJECT_DETECTION.value:
            # Draw labelled bounding boxes in the camera screen
            image_object_predictions = json.loads(payload.message)['image_object_predictions']
            img = st.session_state['img']
            for image_object_prediction in image_object_predictions:
                x1 = image_object_prediction['x1']
                y1 = image_object_prediction['y1']
                x2 = image_object_prediction['x2']
                y2 = image_object_prediction['y2']
                label = f'{image_object_prediction["name"]} {image_object_prediction["score"]}'
                font = cv2.FONT_HERSHEY_SIMPLEX
                (text_width, text_height), baseline = cv2.getTextSize(label, font, fontScale=0.7, thickness=1)
                label_pos = (x1, y1 - 10)  # Put label above the box
                # Draw a filled rectangle as background for the label
                cv2.rectangle(img, (x1, y1 - text_height - baseline), (x1 + text_width, y1), color=(0, 255, 0),thickness=-1)
                # Draw the text (label) on top of the background rectangle
                cv2.putText(img, label, label_pos, font, fontScale=0.7, color=(0, 0, 0), thickness=1)
                # Draw box
                cv2.rectangle(img, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)
            cv2.imshow("Image", img)
            del streamlit_session._session_state['img']
            cv2.waitKey(1)

        message = Message(t=t, content=content, is_user=False, timestamp=datetime.now())
        streamlit_session._session_state['queue'].put(message)
        streamlit_session._handle_rerun_script_request()

    def on_error(ws, error):
        pass

    def on_open(ws):
        pass

    def on_close(ws, close_status_code, close_msg):
        pass

    def on_ping(ws, data):
        pass

    def on_pong(ws, data):
        pass

    user_type = {
        0: 'assistant',
        1: 'user'
    }

    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'queue' not in st.session_state:
        st.session_state['queue'] = queue.Queue()

    if 'websocket' not in st.session_state:
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
        st.session_state['websocket'] = ws

    if 'session_monitoring' not in st.session_state:
        session_monitoring_thread = threading.Thread(target=session_monitoring,
                                                     kwargs={'interval': SESSION_MONITORING_INTERVAL})
        add_script_run_ctx(session_monitoring_thread)
        session_monitoring_thread.start()
        st.session_state['session_monitoring'] = session_monitoring_thread

    if VIDEO_INPUT_ENABLED and 'video_input' not in st.session_state:  # TODO: MAKE THIS OPTIONAL
        video_input_thread = threading.Thread(target=video_input)
        add_script_run_ctx(video_input_thread)
        video_input_thread.start()
        st.session_state['video_input'] = video_input_thread

    ws = st.session_state['websocket']

    with st.sidebar:

        if reset_button := st.button(label="Reset bot"):
            st.session_state['history'] = []
            st.session_state['queue'] = queue.Queue()
            payload = Payload(action=PayloadAction.RESET)
            ws.send(json.dumps(payload, cls=PayloadEncoder))

        if voice_bytes := audio_recorder(text=None, pause_threshold=2):
            if 'last_voice_message' not in st.session_state or st.session_state['last_voice_message'] != voice_bytes:
                st.session_state['last_voice_message'] = voice_bytes
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
            if 'last_file' not in st.session_state or st.session_state['last_file'] != uploaded_file:
                st.session_state['last_file'] = uploaded_file
                bytes_data = uploaded_file.read()
                file_object = File(file_base64=base64.b64encode(bytes_data).decode('utf-8'), file_name=uploaded_file.name, file_type=uploaded_file.type)
                payload = Payload(action=PayloadAction.USER_FILE, message=file_object.get_json_string())
                file_message = Message(t=MessageType.FILE, content=file_object.to_dict(), is_user=True, timestamp=datetime.now())
                st.session_state.history.append(file_message)
                try:
                    ws.send(json.dumps(payload, cls=PayloadEncoder))
                except Exception as e:
                    st.error('Your message could not be sent. The connection is already closed')
    for message in st.session_state['history']:
        with st.chat_message(user_type[message.is_user]):
            if message.type == MessageType.AUDIO:
                st.audio(message.content, format="audio/wav")
            elif message.type == MessageType.FILE:
                file: File = File.from_dict(message.content)
                file_name = file.name
                file_type = file.type
                file_data = base64.b64decode(file.base64.encode('utf-8'))
                st.download_button(label='Download ' + file_name, file_name=file_name, data=file_data, mime=file_type,
                                   key=file_name + str(time.time()))
            elif message.type == MessageType.LOCATION:
                st.map(message.content)
            elif message.type == MessageType.RAG_ANSWER:
                # TODO: Avoid duplicate in history and queue
                st.write(f'🔮 {message.content["answer"]}')
                with st.expander('Details'):
                    st.write(f'This answer has been generated by an LLM: **{message.content["llm_name"]}**')
                    st.write(f'It received the following documents as input to come up with a relevant answer:')
                    if 'docs' in message.content:
                        for i, doc in enumerate(message.content['docs']):
                            st.write(f'**Document {i + 1}/{len(message.content["docs"])}**')
                            st.write(f'- **Source:** {doc["metadata"]["source"]}')
                            st.write(f'- **Page:** {doc["metadata"]["page"]}')
                            st.write(f'- **Content:** {doc["content"]}')
            else:
                st.write(message.content)

    first_message = True
    while not st.session_state['queue'].empty():
        with st.chat_message("assistant"):
            message = st.session_state['queue'].get()
            if hasattr(message, '__len__'):
                t = len(message.content) / 1000 * 3
            else:
                t = 2
            if t > 3:
                t = 3
            elif t < 1 and first_message:
                t = 1
            first_message = False
            if message.type == MessageType.OPTIONS:
                st.session_state['buttons'] = message.content
            elif message.type == MessageType.FILE:
                st.session_state['history'].append(message)
                with st.spinner(''):
                    time.sleep(t)
                file: File = File.from_dict(message.content)
                file_name = file.name
                file_type = file.type
                file_data = base64.b64decode(file.base64.encode('utf-8'))
                st.download_button(label='Download ' + file_name, file_name=file_name, data=file_data, mime=file_type,
                                   key=file_name + str(time.time()))
            elif message.type == MessageType.LOCATION:
                st.session_state['history'].append(message)
                st.map(message.content)
            elif message.type == MessageType.RAG_ANSWER:
                st.session_state['history'].append(message)
                st.write(f'🔮 {message.content["answer"]}')
                with st.expander('Details'):
                    st.write(f'This answer has been generated by an LLM: **{message.content["llm_name"]}**')
                    st.write(f'It received the following documents as input to come up with a relevant answer:')
                    if 'docs' in message.content:
                        for i, doc in enumerate(message.content['docs']):
                            st.write(f'**Document {i + 1}/{len(message.content["docs"])}**')
                            st.write(f'- **Source:** {doc["metadata"]["source"]}')
                            st.write(f'- **Page:** {doc["metadata"]["page"]}')
                            st.write(f'- **Content:** {doc["content"]}')
            elif message.type == MessageType.STR:
                st.session_state['history'].append(message)
                with st.spinner(''):
                    time.sleep(t)
                st.write(message.content)

    if 'buttons' in st.session_state:
        buttons = st.session_state['buttons']
        cols = st.columns(1)
        for i, option in enumerate(buttons):
            if cols[0].button(option):
                with st.chat_message("user"):
                    st.write(option)
                message = Message(t=MessageType.STR, content=option, is_user=True, timestamp=datetime.now())
                st.session_state.history.append(message)
                payload = Payload(action=PayloadAction.USER_MESSAGE,
                                  message=option)
                ws.send(json.dumps(payload, cls=PayloadEncoder))
                del st.session_state['buttons']
                break

    if user_input:
        if 'buttons' in st.session_state:
            del st.session_state['buttons']
        with st.chat_message("user"):
            st.write(user_input)
        message = Message(t=MessageType.STR, content=user_input, is_user=True, timestamp=datetime.now())
        st.session_state.history.append(message)
        payload = Payload(action=PayloadAction.USER_MESSAGE,
                          message=user_input)
        try:
            ws.send(json.dumps(payload, cls=PayloadEncoder))
        except Exception as e:
            st.error('Your message could not be sent. The connection is already closed')

    st.stop()


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
