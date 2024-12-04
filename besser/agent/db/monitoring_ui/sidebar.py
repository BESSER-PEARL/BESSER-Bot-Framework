import streamlit as st
import streamlit_antd_components as sac


def sidebar_menu():
    st.header('BESSER Agentic Framework Monitoring')
    page = sac.menu([
        sac.MenuItem('Home', icon='house-fill'),
        sac.MenuItem('Intent details', icon='chat-left-text-fill'),
        sac.MenuItem('Flow Graph', icon='diagram-3-fill'),
        sac.MenuItem('Table Overview', icon='table'),
    ], open_all=True)
    return page
