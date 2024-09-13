# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/bot-framework") # Replace with your directory path
import logging
import os
import subprocess
import sys
import threading

import streamlit as st
from streamlit.web import cli as stcli

from besser.bot.db.monitoring_ui.db_connection import connect_to_db, close_connection
from besser.bot.db.monitoring_ui.home import home
from besser.bot.db.monitoring_db import MonitoringDB
from besser.bot.db.monitoring_ui.intent_details import intent_details
from besser.bot.db.monitoring_ui.sidebar import sidebar_menu
from besser.bot.db.monitoring_ui.table_overview import table_overview
from besser.bot.db.monitoring_ui.flow_graph import flow_graph

st.set_page_config(layout="wide")


def start_ui(config_path: str = None, host: str = 'localhost', port: int = 8401) -> None:
    def run_monitoring_ui() -> None:
        """Run the Streamlit UI in a dedicated thread."""
        cmd = ["streamlit", "run"]
        if host:
            cmd.extend(["--server.address", host])
        if port:
            cmd.extend(["--server.port", str(port)])
        cmd.append(os.path.abspath(__file__))
        if config_path:
            cmd.append(config_path)
        subprocess.run(cmd)

    thread = threading.Thread(target=run_monitoring_ui)
    logging.info(f'Monitoring UI starting at {host}:{port}')
    thread.start()


def main():
    try:
        # We get the config file path from the script arguments
        config_path = sys.argv[1]
    except Exception as e:
        # If not provided, we use default value
        config_path = '../../test/examples/config.ini'
    if 'monitoring_db' not in st.session_state:
        st.session_state['monitoring_db'] = connect_to_db(config_path)
    with st.sidebar:
        page = sidebar_menu()
        if st.button('Reconnect'):
            close_connection(st.session_state['monitoring_db'])
            st.session_state['monitoring_db'] = connect_to_db(config_path)
    monitoring_db: MonitoringDB = st.session_state['monitoring_db']
    if monitoring_db is not None:
        if page == 'Home':
            home(monitoring_db)
        elif page == 'Intent details':
            intent_details(monitoring_db)
        elif page == 'Flow Graph':
            flow_graph(monitoring_db)
        elif page == 'Table Overview':
            table_overview(monitoring_db)
    else:
        st.error('Could not connect to the monitoring DB')


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        if len(sys.argv) != 4:
            print('ERROR: Wrong arguments')
            print('Usage: python monitoring_ui.py <config_path> <ui_host> <ui_port>')
            print('Example: python monitoring_ui.py config.ini localhost 8401')
            sys.exit(1)
        sys.argv = ["streamlit", "run",
                    "--server.address", sys.argv[2],
                    "--server.port", sys.argv[3],
                    sys.argv[0],
                    sys.argv[1]]
        sys.exit(stcli.main())
