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

if 'messages' not in st.session_state:
    st.session_state['messages'] = []


def reset_bot():
    try:
        response = requests.post(SERVER_URL + 'reset', json={}, headers=headers)
        return response.json()
    except Exception as e:
        return {'history': [(str(e), 0)]}


def get_history():
    try:
        response = requests.post(SERVER_URL + 'history', json={}, headers=headers)
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

elif submit_button and user_input:
    text_container.empty()
    output = query({'message': user_input})
    st.session_state.messages.append((user_input, 1))
    st.session_state.messages.extend([(m, 0) for m in output["answer"]])
else:
    output = get_history()

history = output['history']


for i in range(len(history)-1, -1, -1):
    m = history[i]
    message(m[0], is_user=m[1], avatar_style=avatar_style[m[1]], seed="Aneka", key=str(i))
