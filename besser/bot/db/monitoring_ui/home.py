import streamlit as st
import plotly.express as px


from besser.bot.db.monitoring_db import MonitoringDB, TABLE_INTENT_PREDICTION, TABLE_SESSION, TABLE_CHAT, \
    TABLE_TRANSITION


def home(monitoring_db: MonitoringDB):
    st.header('Home')
    bot_names = bot_filter(monitoring_db)
    col1, col2 = st.columns(2)
    with col1:
        messages_data(monitoring_db, bot_names)
        # TOTAL NUM OF EVENTS (HISTOGRAM/ DONUT)
        # see utterances x each intent (with params), selectbox

    with col2:
        # put a slider at the top to filter the time
        intent_histogram(monitoring_db, bot_names)
        get_matched_intents_ratio(monitoring_db, bot_names)
        event_distribution(monitoring_db, bot_names)


def event_distribution(monitoring_db, bot_names):
    table_transition = monitoring_db.get_table(TABLE_TRANSITION)
    if bot_names:
        table_session = monitoring_db.get_table(TABLE_SESSION)
        # Filter the tables by the specified bots
        table_session = table_session[table_session['bot_name'].isin(bot_names)]
        table_transition = table_transition[table_transition['session_id'].isin(table_session['id'])]
    fig = px.histogram(table_transition, x='event', color='event', title='Events')
    st.plotly_chart(fig, use_container_width=True)


def messages_data(monitoring_db, bot_names):
    table_chat = monitoring_db.get_table(TABLE_CHAT)
    table_session = monitoring_db.get_table(TABLE_SESSION)
    if bot_names:
        # Filter the tables by the specified bots
        table_session = table_session[table_session['bot_name'].isin(bot_names)]
        table_chat = table_chat[table_chat['session_id'].isin(table_session['id'])]
    total_messages = len(table_chat)
    total_sessions = len(table_session)
    total_user_messages = len(table_chat[table_chat['is_user'] == True])
    total_bot_messages = len(table_chat[table_chat['is_user'] == False])

    st.info(f'**Total sessions: {total_sessions}**')
    st.info(f'**Total messages: {total_messages} ({total_user_messages} user and {total_bot_messages} bot)**')
    st.info(f'**Messages per session: {round(total_messages/total_sessions, 3)} ({round(total_user_messages/total_sessions, 3)} user and {round(total_bot_messages/total_sessions, 3)} bot)**')

    data = {'names': ['User', 'Bot'], 'values': [total_user_messages, total_bot_messages]}
    # TODO: SHOW ANOTHER CHART PER TYPE OF MESSAGE (STR, FILE...)
    fig = px.pie(data, values='values', names='names',
                 # color_discrete_sequence=['blue', 'red'],
                 hole=0.5,
                 title='Total messages')
    st.plotly_chart(fig, use_container_width=True)

    fig = px.histogram(table_chat, x='timestamp', color='is_user', title='Number of messages', nbins=40)
    st.plotly_chart(fig, use_container_width=True)


def bot_filter(monitoring_db: MonitoringDB):
    bots = monitoring_db.get_table(TABLE_SESSION)['bot_name'].unique()
    bot_names = st.multiselect(label='Select one or more bots', options=bots, placeholder='All bots')
    return bot_names


def get_matched_intents_ratio(monitoring_db: MonitoringDB, bot_names=[]):
    table_intent_prediction = monitoring_db.get_table(TABLE_INTENT_PREDICTION)
    if bot_names:
        table_session = monitoring_db.get_table(TABLE_SESSION)
        # Filter the tables by the specified bots
        table_session = table_session[table_session['bot_name'].isin(bot_names)]
        table_intent_prediction = table_intent_prediction[table_intent_prediction['session_id'].isin(table_session['id'])]
    value_counts = table_intent_prediction['intent'].value_counts()
    fallback_count = value_counts['fallback_intent'] if 'fallback_intent' in value_counts else 0
    intent_matched_count = len(table_intent_prediction) - fallback_count
    data = {'names': ['Matched', 'Fallback'], 'values': [intent_matched_count, fallback_count]}
    fig = px.pie(data, values='values', names='names',
                 #color_discrete_sequence=['blue', 'red'],
                 hole=0.5,
                 title='Matched intents ratio')
    st.plotly_chart(fig, use_container_width=True)


def intent_histogram(monitoring_db: MonitoringDB, bot_names=[]):
    table_intent_prediction = monitoring_db.get_table(TABLE_INTENT_PREDICTION)
    if bot_names:
        table_session = monitoring_db.get_table(TABLE_SESSION)
        # Filter the tables by the specified bots
        table_session = table_session[table_session['bot_name'].isin(bot_names)]
        table_intent_prediction = table_intent_prediction[table_intent_prediction['session_id'].isin(table_session['id'])]
    fig = px.histogram(table_intent_prediction, x='intent', color='intent', title='Histogram of Intents')
    st.plotly_chart(fig, use_container_width=True)
