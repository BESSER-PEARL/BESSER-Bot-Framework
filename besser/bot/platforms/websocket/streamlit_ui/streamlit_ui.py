import sys
# sys.path.append("/Path/to/directory/bot-framework") # Replace with your directory path

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli

from besser.bot.platforms.websocket.streamlit_ui.chat import load_chat
from besser.bot.platforms.websocket.streamlit_ui.initialization import initialize
from besser.bot.platforms.websocket.streamlit_ui.message_input import message_input
from besser.bot.platforms.websocket.streamlit_ui.sidebar import sidebar


def main():
    try:
        # We get the websocket host and port from the script arguments
        bot_name = sys.argv[1]
    except Exception as e:
        # If they are not provided, we use default values
        bot_name = 'Chatbot Demo'
    st.header(bot_name)
    st.markdown("[Github](https://github.com/BESSER-PEARL/BESSER-Bot-Framework)")

    initialize()
    sidebar()
    load_chat()
    message_input()
    st.stop()


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
