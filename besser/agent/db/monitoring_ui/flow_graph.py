import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from besser.agent.db.monitoring_db import MonitoringDB, TABLE_TRANSITION, TABLE_SESSION
from besser.agent.db.monitoring_ui.home import agent_filter


def flow_graph(monitoring_db: MonitoringDB):
    st.header('Flow Graph')
    agent_names = agent_filter(monitoring_db)
    table_transition = monitoring_db.get_table(TABLE_TRANSITION)
    if agent_names:
        table_session = monitoring_db.get_table(TABLE_SESSION)
        # Filter the tables by the specified agents
        table_session = table_session[table_session['agent_name'].isin(agent_names)]
        table_transition = table_transition[table_transition['session_id'].isin(table_session['id'])]

    nt = Network("700px", "100%", notebook=True, directed=True)
    state_set = set()
    transition_dict = {}
    # TODO: Initial states in another colour, set group=2 in add_node()
    # TODO: SET PHYSICS ATTRS: gravitationalConstant to -12000 and springLength to 200
    for i, transition in table_transition.iterrows():
        source_state = transition['source_state']
        dest_state = transition['dest_state']
        event = transition['event']
        info = transition['info']
        if source_state not in state_set:
            state_set.add(source_state)
            nt.add_node(source_state, group=1)
        if (source_state, dest_state, event, info) not in transition_dict:
            transition_dict[(source_state, dest_state, event, info)] = 1
        else:
            transition_dict[(source_state, dest_state, event, info)] += 1
    if transition_dict:
        max_count = max(transition_dict.values())
        for (source_state, dest_state, event, info), count in transition_dict.items():
            if source_state != dest_state:
                title = event
                if info:
                    title += f'({info})'
                nt.add_edge(source_state, dest_state, title=title, width=count/max_count*10, label=str(count))
            else:
                # TODO: REPLACE THIS, use new table to store body and fallback_body executions per state
                nt.add_edge(source_state, dest_state, title='Fallback', width=count/max_count*10, label=str(count), color='red')
        nt.options.physics.use_barnes_hut({
            'gravity': -12000,  # changed
            'central_gravity': 0.3,
            'spring_length': 200,  # changed
            'spring_strength': 0.04,
            'damping': 0.09,
            'overlap': 0
        })
        # nt.show_buttons(filter_=['physics'])
        # Save html file with network
        #     nt.show('test.html')
        #     HtmlFile = open("test.html", 'r', encoding='utf-8')
        #     source_code = HtmlFile.read()
        source_code = nt.generate_html()
        # Show in streamlit
        components.html(source_code, height=900, width=900)
    else:
        st.warning('There is no data for the selected agents')


