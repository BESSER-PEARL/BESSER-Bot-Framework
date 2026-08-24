"""Tests for session-variable persistence in ``MonitoringDB``."""

import json
import logging

import pytest
from sqlalchemy import Column, MetaData, String, Table, create_engine, insert, select

from baf.core.agent import Agent
from baf.core.session import Session
from baf.db import DB_MONITORING
from baf.db.monitoring_db import MonitoringDB, TABLE_SESSION


class Strings:
    def __init__(self, text, value):
        self.text = text
        self.value = value


@pytest.fixture
def persisted_session(fake_platform):
    agent = Agent("session_agent")
    agent.new_state("initial", initial=True)
    agent._platforms.append(fake_platform)
    session = Session("sid-1", agent, fake_platform, username="alice")

    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    session_table = Table(
        TABLE_SESSION,
        metadata,
        Column("agent_name", String, nullable=False),
        Column("platform_name", String, nullable=False),
        Column("session_id", String, nullable=False),
        Column("variables", String, nullable=True),
    )
    metadata.create_all(engine)
    connection = engine.connect()
    connection.execute(
        insert(session_table).values(
            agent_name=agent.name,
            platform_name=fake_platform.__class__.__name__,
            session_id=session.id,
            variables="{}",
        )
    )
    connection.commit()

    monitoring_db = MonitoringDB()
    monitoring_db.conn = connection
    monitoring_db.connected = True
    agent.set_property(DB_MONITORING, True)
    agent._monitoring_db = monitoring_db
    yield monitoring_db, session, session_table

    connection.close()
    engine.dispose()


def _stored_variables(monitoring_db, session_table):
    variables = monitoring_db.conn.execute(select(session_table.c.variables)).scalar_one()
    return json.loads(variables)


def test_json_compatible_session_variables_persist_unchanged(persisted_session):
    monitoring_db, session, session_table = persisted_session
    expected = {
        "name": "Ada",
        "count": 3,
        "active": True,
        "details": {"roles": ["admin", None], "score": 4.5},
    }
    session.get_dictionary().update(expected)

    monitoring_db.store_session_variables(session)

    assert _stored_variables(monitoring_db, session_table) == expected


def test_non_serializable_variable_is_omitted_with_warning(persisted_session, caplog):
    monitoring_db, session, session_table = persisted_session

    with caplog.at_level(logging.WARNING, logger="BESSER Agentic Framework"):
        session.set("custom", Strings("secret", False))
        session.set("valid", {"items": [1, 2]})

    assert _stored_variables(monitoring_db, session_table) == {"valid": {"items": [1, 2]}}
    assert session.get("custom").text == "secret"
    assert "Session variable 'custom'" in caplog.text
    assert "Strings is not JSON serializable" in caplog.text
    assert "secret" not in caplog.text


def test_nested_non_serializable_value_omits_whole_variable(persisted_session, caplog):
    monitoring_db, session, session_table = persisted_session

    with caplog.at_level(logging.WARNING, logger="BESSER Agentic Framework"):
        session.set("nested", {"items": ["safe", Strings("private", True)]})
        session.set("valid", "kept")

    assert _stored_variables(monitoring_db, session_table) == {"valid": "kept"}
    assert "Session variable 'nested'" in caplog.text
    assert "Strings is not JSON serializable" in caplog.text
    assert "private" not in caplog.text


def test_circular_session_variable_is_omitted(persisted_session, caplog):
    monitoring_db, session, session_table = persisted_session
    circular = []
    circular.append(circular)

    with caplog.at_level(logging.WARNING, logger="BESSER Agentic Framework"):
        session.set("circular", circular)
        session.set("valid", "kept")

    assert _stored_variables(monitoring_db, session_table) == {"valid": "kept"}
    assert "Session variable 'circular'" in caplog.text
    assert "Circular reference detected" in caplog.text


def test_persistence_errors_are_not_swallowed(persisted_session, monkeypatch):
    monitoring_db, session, _ = persisted_session
    session.get_dictionary()["valid"] = "value"

    def raise_database_error(_statement):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(monitoring_db, "run_statement", raise_database_error)

    with pytest.raises(RuntimeError, match="database unavailable"):
        monitoring_db.store_session_variables(session)


def test_valid_stored_variables_are_restored_unchanged(persisted_session):
    monitoring_db, session, session_table = persisted_session
    expected = {"name": "Ada", "details": {"items": [1, None, True]}}
    monitoring_db.conn.execute(session_table.update().values(variables=json.dumps(expected)))
    monitoring_db.conn.commit()

    monitoring_db.load_session_variables(session)

    assert session.get_dictionary() == expected
