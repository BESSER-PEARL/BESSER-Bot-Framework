from besser.bot.core.property import Property

# Definition of the bot properties within the websocket_platform section

SECTION_WEBSOCKET = 'websocket_platform'

WEBSOCKET_HOST = Property(SECTION_WEBSOCKET, 'websocket.host', str, 'localhost')
WEBSOCKET_PORT = Property(SECTION_WEBSOCKET, 'websocket.port', int, 8765)
STREAMLIT_HOST = Property(SECTION_WEBSOCKET, 'streamlit.host', str, 'localhost')
STREAMLIT_PORT = Property(SECTION_WEBSOCKET, 'streamlit.port', int, 5000)
