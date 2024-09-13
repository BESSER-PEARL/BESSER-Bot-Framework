import atexit
import logging
from configparser import ConfigParser
from typing import Any

from sqlalchemy import create_engine

from besser.bot.core.property import Property
from besser.bot.db import DB_MONITORING_DIALECT, DB_MONITORING_HOST, DB_MONITORING_PORT, DB_MONITORING_DATABASE, \
    DB_MONITORING_USERNAME, DB_MONITORING_PASSWORD
from besser.bot.db.monitoring_db import MonitoringDB


def get_property(config: ConfigParser, prop: Property) -> Any:
    if prop.type == str:
        getter = config.get
    elif prop.type == bool:
        getter = config.getboolean
    elif prop.type == int:
        getter = config.getint
    elif prop.type == float:
        getter = config.getfloat
    else:
        return None
    return getter(prop.section, prop.name, fallback=prop.default_value)


def close_connection(monitoring_db: MonitoringDB):
    logging.info('Closing DB connection...')
    if monitoring_db is not None:
        monitoring_db.close_connection()


def connect_to_db(config_path: str):
    # Path to the configuration file where the DB credentials are defined
    config: ConfigParser = ConfigParser()
    read_files = config.read(config_path)
    if read_files:
        monitoring_db = MonitoringDB()
        try:
            dialect = get_property(config, DB_MONITORING_DIALECT)
            host = get_property(config, DB_MONITORING_HOST)
            port = get_property(config, DB_MONITORING_PORT)
            database = get_property(config, DB_MONITORING_DATABASE)
            username = get_property(config, DB_MONITORING_USERNAME)
            password = get_property(config, DB_MONITORING_PASSWORD)
            url = f"{dialect}://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(url)
            monitoring_db.conn = engine.connect()
            atexit.register(close_connection, monitoring_db)
            logging.info('Connected to DB')
            return monitoring_db
        except Exception as e:
            logging.error(f"An error occurred while trying to connect to the monitoring DB in the monitoring UI. "
                          f"See the attached exception:")
            logging.error(e)
            return None
    else:
        logging.error(f"The file {config_path} could not be read")
