import streamlit as st

from besser.agent.db.monitoring_db import MonitoringDB, TABLE_SESSION, TABLE_INTENT_PREDICTION, TABLE_PARAMETER, \
    TABLE_TRANSITION, TABLE_CHAT
from besser.agent.db.monitoring_ui.utils import filter_df


def table_overview(monitoring_db: MonitoringDB):

    st.subheader(f'Table {TABLE_CHAT}')
    st.dataframe(filter_df(monitoring_db.get_table(TABLE_CHAT), TABLE_CHAT), use_container_width=True)

    st.subheader(f'Table {TABLE_SESSION}')
    st.dataframe(filter_df(monitoring_db.get_table(TABLE_SESSION), TABLE_SESSION), use_container_width=True)

    st.subheader(f'Table {TABLE_INTENT_PREDICTION}')
    st.dataframe(filter_df(monitoring_db.get_table(TABLE_INTENT_PREDICTION), TABLE_INTENT_PREDICTION), use_container_width=True)

    st.subheader(f'Table {TABLE_PARAMETER}')
    st.dataframe(filter_df(monitoring_db.get_table(TABLE_PARAMETER), TABLE_PARAMETER), use_container_width=True)

    st.subheader(f'Table {TABLE_TRANSITION}')
    st.dataframe(filter_df(monitoring_db.get_table(TABLE_TRANSITION), TABLE_TRANSITION), use_container_width=True)

