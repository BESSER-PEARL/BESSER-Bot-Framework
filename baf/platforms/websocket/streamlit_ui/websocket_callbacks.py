from __future__ import annotations

import base64
import json
from datetime import datetime
from io import StringIO

import numpy as np
import pandas as pd

from baf.core.message import MessageType, Message
from baf.exceptions.logger import logger
from baf.platforms.payload import PayloadAction, Payload
from baf.platforms.websocket.streamlit_ui.reasoning import (
    append_reasoning_step,
    apply_task_list_update,
)
from baf.platforms.websocket.streamlit_ui.session_management import get_streamlit_session
from baf.platforms.websocket.streamlit_ui.vars import QUEUE, HISTORY, WEBSOCKET_READY

try:
    import cv2
except ImportError:
    logger.warning("cv2 dependencies in websocket_callbacks.py could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")
try:
    import plotly
except ImportError:
    logger.warning("plotly dependencies in websocket_callbacks.py could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")


def on_message(ws, payload_str):
    # https://github.com/streamlit/streamlit/issues/2838
    streamlit_session = get_streamlit_session()
    payload: Payload = Payload.decode(payload_str)
    content = None
    is_user = False
    if payload.action == PayloadAction.AGENT_REPLY_STR.value:
        content = payload.message
        t = MessageType.STR
    elif payload.action == PayloadAction.USER_MESSAGE.value:
        content = payload.message
        t = MessageType.STR
        is_user = True
    elif payload.action == PayloadAction.AGENT_REPLY_MARKDOWN.value:
        content = payload.message
        t = MessageType.MARKDOWN
    elif payload.action == PayloadAction.AGENT_REPLY_HTML.value:
        content = payload.message
        t = MessageType.HTML
    elif payload.action == PayloadAction.AGENT_REPLY_FILE.value:
        content = payload.message
        t = MessageType.FILE
    elif payload.action == PayloadAction.AGENT_REPLY_AUDIO.value:
        # Encode the string back to bytes (using utf-8 or ascii)
        base64_bytes = payload.message['audio_data_base64'].encode('utf-8')
        # Decode the Base64 bytes to get the original raw audio bytes
        audio_bytes = base64.b64decode(base64_bytes)
        # Convert the raw bytes back to a NumPy array using np.frombuffer
        reconstructed_array_flat = np.frombuffer(audio_bytes, dtype=np.dtype(payload.message['metadata']['dtype']))
        # Verify size consistency
        shape = payload.message['metadata']['shape']
        expected_size = np.prod(shape)
        if reconstructed_array_flat.size != expected_size:
            logger.error(
                "Decoded data size (%s) does not match expected size from shape %s (%s). Check dtype and shape.",
                reconstructed_array_flat.size,
                shape,
                expected_size,
            )
            logger.error("Error during decoding")
            logger.error("Ensure the provided dtype and shape match the original array used for encoding.")
            return
        # Reshape the flat array back to its original shape
        reconstructed_array = reconstructed_array_flat.reshape(shape)
        # recreate original dictionary
        tts_dict = {
            "audio": reconstructed_array,
            "sampling_rate": payload.message['metadata']['sample_rate']
        }
        content = tts_dict
        t = MessageType.AUDIO
    elif payload.action == PayloadAction.AGENT_REPLY_IMAGE.value:
        decoded_data = base64.b64decode(payload.message)  # Decode base64 back to bytes
        np_data = np.frombuffer(decoded_data, np.uint8)  # Convert bytes to numpy array
        img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)  # Decode numpy array back to image
        content = img
        t = MessageType.IMAGE
    elif payload.action == PayloadAction.AGENT_REPLY_DF.value:
        content = pd.read_json(StringIO(payload.message))
        t = MessageType.DATAFRAME
    elif payload.action == PayloadAction.AGENT_REPLY_PLOTLY.value:
        content = plotly.io.from_json(payload.message)
        t = MessageType.PLOTLY
    elif payload.action == PayloadAction.AGENT_REPLY_LOCATION.value:
        content = {
            'latitude': [payload.message['latitude']],
            'longitude': [payload.message['longitude']]
        }
        t = MessageType.LOCATION
    elif payload.action == PayloadAction.AGENT_REPLY_OPTIONS.value:
        t = MessageType.OPTIONS
        d = json.loads(payload.message)
        content = []
        for button in d.values():
            content.append(button)
    elif payload.action == PayloadAction.AGENT_REPLY_RAG.value:
        t = MessageType.RAG_ANSWER
        content = payload.message
    elif payload.action == PayloadAction.AGENT_REPLY_REASONING_STEP.value:
        # Streamed reasoning step events are folded into a single
        # REASONING_TRACE message in HISTORY so the UI renders one
        # collapsible expander per loop instead of one chat row per step.
        # All trace aggregation + rendering lives in
        # baf.platforms.websocket.streamlit_ui.reasoning.
        append_reasoning_step(streamlit_session, payload.message)
        streamlit_session._handle_rerun_script_request()
        return
    elif payload.action == PayloadAction.AGENT_REPLY_TASK_LIST_UPDATE.value:
        # Task list snapshots also fold into the in-progress trace.
        apply_task_list_update(streamlit_session, payload.message)
        streamlit_session._handle_rerun_script_request()
        return
    if content is not None:
        message = Message(t=t, content=content, is_user=is_user, timestamp=datetime.now())
        try:
            if payload.history:
                streamlit_session._session_state[HISTORY].append(message)
            else:
                streamlit_session._session_state[QUEUE].put(message)
        except Exception as e:
            logger.error(f"Error putting message in queue: {e}")

    streamlit_session._handle_rerun_script_request()


def _set_ready_state(value: bool):
    try:
        streamlit_session = get_streamlit_session()
        if streamlit_session is None:
            logger.info("Streamlit session is closed already. Gracefully skipping state update.")
            return
        
        # Check if session state still exists and is accessible
        if not hasattr(streamlit_session, '_session_state') or streamlit_session._session_state is None:
            logger.info("Session state has shut down.")
            return
        
        # Safely update the ready state
        streamlit_session._session_state[WEBSOCKET_READY] = value
        streamlit_session._handle_rerun_script_request()
    except RuntimeError as exc:
        # RuntimeError occurs when trying to access session during shutdown
        logger.error(f"RuntimeError during websocket ready state update (likely shutdown): {exc}")
    except Exception as exc:
        logger.error(f"Failed to update websocket ready state: {exc}")


def on_error(ws, error):
    logger.error(f"WebSocket error: {error}")


def on_open(ws):
    _set_ready_state(True)


def on_close(ws, close_status_code, close_msg):
    try:
        _set_ready_state(False)
    except Exception:
        logger.info(f"Websocket connection is closed with code {close_status_code}")


def on_ping(ws, data):
    pass


def on_pong(ws, data):
    pass
