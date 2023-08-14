import logging

from websockets.exceptions import ConnectionClosedError
from websockets.sync.server import ServerConnection, serve
from besser.bot.server.Payload import Payload


def message_handler(bot, conn: ServerConnection):
    # TODO close session when streamlit browser is closed
    session = bot.new_session(conn)
    try:
        for payload_str in conn:
            payload: Payload = Payload.decode(payload_str)
            if payload.action == Payload.USER_MESSAGE:
                bot.receive_message(session, payload.message)
            elif payload.action == Payload.RESET:
                bot.reset(session)
    except ConnectionClosedError:
        logging.error(f'The client closed unexpectedly')
    except Exception as e:
        logging.error("Server Error:", e)
    finally:
        logging.info(f'Session finished')
        bot.delete_session(session)


# Create a closure that captures the extra parameter and returns the handler function.
def handler_closure(bot):
    def handler(websocket):
        return message_handler(bot, websocket)
    return handler


class Server:

    def __init__(self, bot):
        self.bot = bot
        self.host = None
        self.port = None
        self.websocket_server = None

    def initialize(self):
        self.host = self.bot.config.get('server', 'host', fallback='localhost')
        self.port = self.bot.config.getint('server', 'port', fallback=8765)
        self.websocket_server = serve(handler_closure(bot=self.bot), self.host, self.port)

    def run(self):
        self.websocket_server.serve_forever()
