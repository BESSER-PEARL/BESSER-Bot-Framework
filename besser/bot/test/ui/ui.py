import uuid

import streamlit as st
from streamlit_chat import message
import requests

st.set_page_config(
    page_title="Streamlit Chat - Demo",
    page_icon=":robot:"
)

SERVER_URL = 'http://127.0.0.1:5000/'

headers = {
    'Content-Type': 'application/json'
}
avatar_style = ["bottts-neutral", "big-ears-neutral"]

st.header("Chat Demo")
st.markdown("[Github](https://github.com/BESSER-PEARL/bot-framework)")

text_container = st.container()
response_container = st.container()

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())
    output = requests.post(SERVER_URL + 'new_session', json={'user_id': st.session_state['user_id']}, headers=headers).json()
    st.session_state.history.extend([(m, 0) for m in output["answer"]])


def reset_bot():
    try:
        response = requests.post(SERVER_URL + 'reset', json={}, headers=headers)
        return response.json()
    except Exception as e:
        return {'history': [(str(e), 0)]}


def get_history():
    try:
        response = requests.post(SERVER_URL + 'history', json={'user_id': st.session_state['user_id']}, headers=headers)
        return response.json()
    except Exception as e:
        return {'history': [(str(e), 0)]}


def query(payload):
    try:
        response = requests.post(SERVER_URL + 'message', json=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {'history': [(str(e), 0)]}


with text_container:
    with st.form(key="prompt_input", clear_on_submit=True):
        user_input = st.text_input("You:", key="input")
        submit_button = st.form_submit_button(label="Send")
        reset_button = st.form_submit_button(label="Reset")

if reset_button:
    output = reset_bot()
    st.session_state.history = output['history']
elif submit_button and user_input:
    text_container.empty()
    output = query({
        'user_id': st.session_state['user_id'],
        'message': user_input})
    st.session_state.history.append((user_input, 1))
    st.session_state.history.extend([(m, 0) for m in output["answer"]])


for i in range(len(st.session_state.history)-1, -1, -1):
    m = st.session_state.history[i]
    message(m[0], is_user=m[1], avatar_style=avatar_style[m[1]], seed="Aneka", key=str(i))
