import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd
from sqlalchemy import Connection, create_engine, Column, String, Integer, UniqueConstraint, ForeignKey, DateTime, \
    Float, MetaData, insert, Table, select, Executable, CursorResult, desc, Boolean
from sqlalchemy.orm import declarative_base

from besser.bot.core.message import Message
from besser.bot.core.session import Session
from besser.bot.core.state import State
from besser.bot.core.transition import Transition
from besser.bot.db import DB_MONITORING_DIALECT, DB_MONITORING_PORT, DB_MONITORING_HOST, DB_MONITORING_DATABASE, \
    DB_MONITORING_USERNAME, DB_MONITORING_PASSWORD
from besser.bot.library.event.event_library import intent_matched, variable_matches_operation
from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


TABLE_SESSION = 'session'
"""The name of the database table that contains the session records"""

TABLE_INTENT_PREDICTION = 'intent_prediction'
"""The name of the database table that contains the intent prediction records"""

TABLE_PARAMETER = 'parameter'
"""The name of the database table that contains the parameter records"""

TABLE_TRANSITION = 'transition'
"""The name of the database table that contains the transition records"""

TABLE_CHAT = 'chat'
"""The name of the database table that contains the chat records"""


class MonitoringDB:
    """This class is an interface to connect to a database where user interactions with the bot are stored to monitor
    the bot for later analysis.

    Attributes:
        conn (sqlalchemy.Connection): The connection to the monitoring database
        connected (bool): Whether there is an active connection to the monitoring database or not
    """

    def __init__(self):
        self.conn: Connection = None
        self.connected: bool = False

    def connect_to_db(self, bot: 'Bot') -> None:
        """Connect to the monitoring database.

        Args:
            bot (Bot): The bot that contains the database-related properties.
        """
        try:
            dialect = bot.get_property(DB_MONITORING_DIALECT)
            username = bot.get_property(DB_MONITORING_USERNAME)
            password = bot.get_property(DB_MONITORING_PASSWORD)
            host = bot.get_property(DB_MONITORING_HOST)
            port = bot.get_property(DB_MONITORING_PORT)
            database = bot.get_property(DB_MONITORING_DATABASE)
            url = f"{dialect}://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(url)
            self.conn = engine.connect()
            self.connected = True
        except Exception as e:
            logging.error(f"An error occurred while trying to connect to the monitoring DB in bot '{bot.name}'. "
                          f"See the attached exception:")
            logging.error(e)

    def initialize_db(self) -> None:
        """Initialize the monitoring database, creating the tables if necessary."""
        Base = declarative_base()  # Define a declarative base

        # Define the table schemas
        class TableSession(Base):
            __tablename__ = TABLE_SESSION
            id = Column(Integer, primary_key=True, autoincrement=True)
            bot_name = Column(String, nullable=False)
            session_id = Column(String, nullable=False)
            platform_name = Column(String, nullable=False)
            timestamp = Column(DateTime, nullable=False)
            __table_args__ = (
                UniqueConstraint('bot_name', 'session_id'),
            )

        class TableIntentPrediction(Base):
            __tablename__ = TABLE_INTENT_PREDICTION
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=False)
            message = Column(String, nullable=False)
            timestamp = Column(DateTime, nullable=False)
            intent_classifier = Column(String, nullable=False)
            intent = Column(String, nullable=False)
            score = Column(Float, nullable=False)

        class TableParameter(Base):
            __tablename__ = TABLE_PARAMETER
            id = Column(Integer, primary_key=True, autoincrement=True)
            intent_prediction_id = Column(Integer, ForeignKey(f'{TABLE_INTENT_PREDICTION}.id'), nullable=False)
            name = Column(String, nullable=False)
            value = Column(String)
            info = Column(String)

        class TableTransition(Base):
            __tablename__ = TABLE_TRANSITION
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=False)
            source_state = Column(String, nullable=False)
            dest_state = Column(String, nullable=False)
            event = Column(String, nullable=False)
            info = Column(String)
            timestamp = Column(DateTime, nullable=False)

        class TableChat(Base):
            __tablename__ = TABLE_CHAT
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=False)
            type = Column(String, nullable=False)
            content = Column(String, nullable=False)
            is_user = Column(Boolean, nullable=False)
            timestamp = Column(DateTime, nullable=False)

        Base.metadata.create_all(self.conn)
        self.conn.commit()

    def insert_session(self, session: Session) -> None:
        """Insert a new session record into the sessions table of the monitoring database.

        Args:
            session (Session): the session to insert into the database
        """
        table = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt = insert(table).values(
            bot_name=session._bot.name,
            session_id=session.id,
            platform_name=session.platform.__class__.__name__,
            timestamp=datetime.now(),
        )
        self.run_statement(stmt)

    def insert_intent_prediction(self, session: Session, state: State) -> None:
        """Insert a new intent prediction record into the intent predictions table of the monitoring database.

        Args:
            session (Session): the session containing the predicted intent to insert into the database
            state (State): the state where the intent prediction took place (the session's current state may have
                changed since the intent prediction, so we need it as argument)
        """
        table = Table(TABLE_INTENT_PREDICTION, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        if state not in session._bot.nlp_engine._intent_classifiers and session.predicted_intent.intent.name == 'fallback_intent':
            intent_classifier = 'None'
        elif isinstance(session._bot.nlp_engine._intent_classifiers[state], LLMIntentClassifier):
            intent_classifier = state.ic_config.llm_name
        else:
            intent_classifier = session._bot.nlp_engine._intent_classifiers[state].__class__.__name__,
        stmt = insert(table).values(
            session_id=int(session_entry['id'][0]),
            message=session.message,
            timestamp=datetime.now(),
            intent_classifier=intent_classifier,
            intent=session.predicted_intent.intent.name,
            score=float(session.predicted_intent.score)
        )
        result = self.conn.execute(stmt.returning(table.c.id))  # Not committed until all parameters have been inserted
        intent_prediction_id = int(result.fetchone()[0])
        table = Table(TABLE_PARAMETER, MetaData(), autoload_with=self.conn)
        rows_to_insert = [
            {
                'intent_prediction_id': intent_prediction_id,
                'name': matched_parameter.name,
                'value': matched_parameter.value,
                'info': str(matched_parameter.info),
            } for matched_parameter in session.predicted_intent.matched_parameters
        ]
        if rows_to_insert:
            stmt = insert(table).values(rows_to_insert)
            self.run_statement(stmt)
        else:
            self.conn.commit()

    def insert_transition(self, session: Session, transition: Transition) -> None:
        """Insert a new transition record into the transitions table of the monitoring database.

        Args:
            session (Session): the session the transition belongs to
            transition (Transition): the transition to insert into the database
        """
        table = Table(TABLE_TRANSITION, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        if transition.event == intent_matched:
            transition_info = transition.event_params['intent'].name
        elif transition.event == variable_matches_operation:
            transition_info = f'{transition.event_params["var_name"]} {transition.event_params["operation"].__name__} {transition.event_params["target"]}'
        else:
            transition_info = ''
        stmt = insert(table).values(
            session_id=int(session_entry['id'][0]),
            source_state=transition.source.name,
            dest_state=transition.dest.name,
            event=transition.event.__name__,
            info=transition_info,
            timestamp=datetime.now(),
        )
        self.run_statement(stmt)

    def insert_chat(self, session: Session, message: Message) -> None:
        """Insert a new record into the chat table of the monitoring database.

        Args:
            session (Session): the session the transition belongs to
            message (Message): the message to insert into the database
        """
        table = Table(TABLE_CHAT, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        stmt = insert(table).values(
            session_id=int(session_entry['id'][0]),
            type=message.type.value,
            content=message.content,
            is_user=message.is_user,
            timestamp=message.timestamp,
        )
        self.run_statement(stmt)

    def select_session(self, session: Session) -> pd.DataFrame:
        """Retrieves a session record from the sessions table of the database.

        Args:
            session (Session): the session to get from the database

        Returns:
            pandas.DataFrame: the session record, should be a 1 row DataFrame

        """
        table = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt = select(table).where(
            table.c.bot_name == session._bot.name,
            table.c.platform_name == session.platform.__class__.__name__,
            table.c.session_id == session.id
        )
        return pd.read_sql_query(stmt, self.conn)

    def select_chat(self, session: Session, n: int) -> pd.DataFrame:
        """Retrieves a conversation history from the chat table of the database.

        Args:
            session (Session): the session to get from the database
            n (int or None): the number of messages to get (from the most recents). If none is provided, gets all the
                messages
        Returns:
            pandas.DataFrame: the session record, should be a 1 row DataFrame

        """
        table = Table(TABLE_CHAT, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        stmt = (select(table).where(
            table.c.session_id == int(session_entry['id'][0])
        ))
        if n:
            stmt = stmt.order_by(desc(table.c.id)).limit(n)
        return pd.read_sql_query(stmt, self.conn).sort_values(by='id')

    def run_statement(self, stmt: Executable) -> CursorResult[Any] | None:
        """Executes a SQL statement.

        Args:
            stmt (sqlalchemy.Executable): the SQL statement

        Returns:
            sqlalchemy.CursorResult[Any] | None: the result of the SQL statement
        """
        try:
            result = self.conn.execute(stmt)
            self.conn.commit()
            return result
        except Exception as e:
            logging.error(e)
            self.conn.rollback()
            return None

    def get_table(self, table_name: str) -> pd.DataFrame:
        """Gets all the content of a database table (i.e., SELECT * FROM table_name).

        Args:
            table_name: the name of the table

        Returns:
            pandas.DataFrame: the table in a dataframe
        """
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql_query(query, self.conn)

    def close_connection(self) -> None:
        """Close the connection to the monitoring database"""
        self.conn.close()
        self.conn.engine.dispose()
        self.connected = False
