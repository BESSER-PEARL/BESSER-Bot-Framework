"""Definition of the agent properties within the ``db`` (Database) section"""

from besser.agent.core.property import Property

SECTION_DB = 'db'

DB_MONITORING = Property(SECTION_DB, 'db.monitoring', bool, False)
"""
Whether to use the monitoring database or not. If true, all the ``DB_MONITORING_*`` properties must be properly set.

name: ``db.monitoring``

type: ``bool``

default value: ``False``
"""

DB_MONITORING_DIALECT = Property(SECTION_DB, 'db.monitoring.dialect', str, None)
"""
The database dialect (e.g., ``postgresql``).

name: ``db.monitoring.dialect``

type: ``str``

default value: ``None``
"""

DB_MONITORING_HOST = Property(SECTION_DB, 'db.monitoring.host', str, None)
"""
The database host address (e.g., ``localhost``).

name: ``db.monitoring.host``

type: ``str``

default value: ``None``
"""

DB_MONITORING_PORT = Property(SECTION_DB, 'db.monitoring.port', int, None)
"""
The database port (e.g., ``5432``).

name: ``db.monitoring.port``

type: ``int``

default value: ``None``
"""

DB_MONITORING_DATABASE = Property(SECTION_DB, 'db.monitoring.database', str, None)
"""
The database name.

name: ``db.monitoring.database``

type: ``str``

default value: ``None``
"""

DB_MONITORING_USERNAME = Property(SECTION_DB, 'db.monitoring.username', str, None)
"""
The database username.

name: ``db.monitoring.username``

type: ``str``

default value: ``None``
"""

DB_MONITORING_PASSWORD = Property(SECTION_DB, 'db.monitoring.password', str, None)
"""
The database password.

name: ``db.monitoring.password``

type: ``str``

default value: ``None``
"""
