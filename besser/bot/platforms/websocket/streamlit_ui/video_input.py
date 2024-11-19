import base64
import json
import time

import cv2
from streamlit.runtime import Runtime

from besser.bot.platforms.payload import Payload, PayloadAction, PayloadEncoder
from besser.bot.platforms.websocket.streamlit_ui.session_management import get_streamlit_session
from besser.bot.platforms.websocket.streamlit_ui.vars import VIDEO_INPUT_INTERVAL


def video_input():
    """This function periodically sends images to the bot at a specific frequency (defined by VIDEO_INPUT_INTERVAL, in
    seconds)"""
    # TODO: FINISH WHEN SESSION IS CLOSED
    runtime: Runtime = Runtime.instance()
    session = get_streamlit_session()
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    while True:
        if 'last_img' not in session._session_state:
            # Last image released, proceed with the next frame
            ws = session._session_state['websocket']
            success, img = cap.read()
            if success:
                retval, buffer = cv2.imencode('.jpg', img)  # Encode as JPEG
                base64_img = base64.b64encode(buffer).decode('utf-8')
                payload = Payload(action=PayloadAction.USER_IMAGE,
                                  message=base64_img)
                try:
                    ws.send(json.dumps(payload, cls=PayloadEncoder))
                    session.session_state['last_img'] = img
                except Exception as e:
                    print('Your message (image from video input) could not be sent. The connection is already closed')
                    cap.release()
                    break
        elif not runtime.is_active_session(session.id):
            cap.release()
            break
        time.sleep(VIDEO_INPUT_INTERVAL)
