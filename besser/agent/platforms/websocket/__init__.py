"""Definition of the agent properties within the ``websocket_platform`` section:"""

from besser.agent.core.property import Property

SECTION_WEBSOCKET = 'websocket_platform'

WEBSOCKET_HOST = Property(SECTION_WEBSOCKET, 'websocket.host', str, 'localhost')
"""
The WebSocket host address. An agent has a WebSocket server that has to establish connection with a WebSocket client.

name: ``websocket.host``

type: ``str``

default value: ``localhost``
"""

WEBSOCKET_PORT = Property(SECTION_WEBSOCKET, 'websocket.port', int, 8765)
"""
The WebSocket address port. The WebSocket address is composed by a host name and a port

name: ``websocket.port``

type: ``int``

default value: ``8765``
"""

WEBSOCKET_MAX_SIZE = Property(SECTION_WEBSOCKET, 'websocket.max_size', int, None)
"""
WebSocket's maximum size of incoming messages, in bytes. :obj:`None` disables the limit.

name: ``websocket.max_size``

type: ``int``

default value: ``None``
"""

STREAMLIT_HOST = Property(SECTION_WEBSOCKET, 'streamlit.host', str, 'localhost')
"""
The Streamlit UI host address. If you are using our default UI, you must define its address where you can access and 
interact with the agent.

name: ``streamlit.host``

type: ``str``

default value: ``localhost``
"""

STREAMLIT_PORT = Property(SECTION_WEBSOCKET, 'streamlit.port', int, 5000)
"""
The Streamlit UI address port. The Streamlit UI address is composed by a host name and a port

name: ``streamlit.port``

type: ``int``

default value: ``5000``
"""

