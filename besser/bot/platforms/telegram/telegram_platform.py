import asyncio
import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, BaseHandler, CommandHandler, ContextTypes, MessageHandler, \
    filters

from besser.bot.core.session import Session
from besser.bot.exceptions.exceptions import PlatformMismatchError
from besser.bot.platforms import telegram
from besser.bot.platforms.payload import Payload, PayloadAction
from besser.bot.platforms.platform import Platform

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class TelegramPlatform(Platform):
    """The Telegram Platform allows a bot to interact via Telegram.

    It includes a `message handler` to handle all text inputs except commands (i.e. messages starting with '/')
    and a `reset handler`, triggered by the `/reset` command, to reset the bot session.

    Args:
        bot (Bot): the bot the platform belongs to

    Attributes:
        _bot (Bot): The bot the platform belongs to
        _telegram_app (Application): The Telegram Application
        _event_loop (asyncio.AbstractEventLoop): The event loop that runs the asynchronous tasks of the Telegram
            Application
    """
    def __init__(self, bot: 'Bot'):
        super().__init__()
        self._bot: 'Bot' = bot
        self._telegram_app: Application = None
        self._event_loop: asyncio.AbstractEventLoop = None
        self._handlers: list[BaseHandler] = []

        async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            session = self._bot.get_session(session_id)
            if session is None:
                self._bot.new_session(session_id, self)
            else:
                text = update.message.text
                self._bot.receive_message(session.id, text)

        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
        self._handlers.append(message_handler)

        # Handler for reset command
        async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            self._bot.reset(session_id)

        reset_handler = CommandHandler('reset', reset)
        self._handlers.append(reset_handler)

    @property
    def telegram_app(self):
        """telegram.ext._application.Application: The Telegram app."""
        return self._telegram_app

    def initialize(self) -> None: # Hide Info logging messages
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self._telegram_app = ApplicationBuilder().token(
            self._bot.get_property(telegram.TELEGRAM_TOKEN)).build()
        self._telegram_app.add_handlers(self._handlers)
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

    def start(self) -> None:
        logging.info(f'{self._bot.name}\'s TelegramPlatform starting')
        self.running = True
        self._telegram_app.run_polling(stop_signals=None)

    def stop(self):
        self._event_loop.stop()
        self.running = False
        logging.info(f'{self._bot.name}\'s TelegramPlatform stopped')

    def _send(self, session_id: str, payload: Payload) -> None:
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(self._telegram_app.bot.send_message(chat_id=session_id, text=payload.message),
                                         loop)

    def reply(self, session: Session, message: str) -> None:
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.chat_history.append((message, 0))
        payload = Payload(action=PayloadAction.BOT_REPLY_STR,
                          message=message)
        self._send(session.id, payload)

    def add_handler(self, handler: BaseHandler) -> None:
        """
        Add a custom Telegram handler for the bot.

        Args:
            handler (telegram.ext.BaseHandler): the handler to add
        """
        self._handlers.append(handler)
