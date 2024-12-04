import streamlit as st


from besser.agent.db.monitoring_db import MonitoringDB, TABLE_INTENT_PREDICTION, TABLE_SESSION
from besser.agent.db.monitoring_ui.home import agent_filter


def intent_details(monitoring_db: MonitoringDB):
    st.header('Intent details')
    agent_names = agent_filter(monitoring_db)
    table_intent_prediction = monitoring_db.get_table(TABLE_INTENT_PREDICTION)
    if agent_names:
        table_session = monitoring_db.get_table(TABLE_SESSION)
        # Filter the tables by the specified agents
        table_session = table_session[table_session['agent_name'].isin(agent_names)]
        table_intent_prediction = table_intent_prediction[
            table_intent_prediction['session_id'].isin(table_session['id'])]
    intent = st.selectbox('Select an intent', table_intent_prediction['intent'].unique())
    table_intent_prediction = table_intent_prediction[table_intent_prediction['intent'] == intent]
    st.subheader(f'Average score: {table_intent_prediction["score"].mean()}')
    st.dataframe(table_intent_prediction[['timestamp', 'message', 'score', 'intent_classifier']], use_container_width=True)
