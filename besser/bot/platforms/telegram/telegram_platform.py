import asyncio
import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, BaseHandler, CommandHandler, ContextTypes, MessageHandler, \
    filters

from besser.bot.core.session import Session
from besser.bot.exceptions.exceptions import PlatformMismatchError
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
    """
    def __init__(self, bot: 'Bot'):
        super().__init__()
        self._bot: 'Bot' = bot
        self._telegram_app: Application = ApplicationBuilder().token(
            self._bot.config.get('telegram', 'token', fallback=None)).build()

        # Handler for text messages
        async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            session = self._bot.get_session(session_id)
            if session is None:
                self._bot.new_session(session_id, self)
            else:
                text = update.message.text
                self._bot.receive_message(session.id, text)
        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
        self._telegram_app.add_handler(message_handler)

        # Handler for reset command
        async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            self._bot.reset(session_id)
        reset_handler = CommandHandler('reset', reset)
        self._telegram_app.add_handler(reset_handler)

    @property
    def telegram_app(self):
        """:class:`telegram.ext._application.Application`: The Telegram app."""
        return self._telegram_app

    def run(self) -> None:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logging.info(f'{self._bot.name}\'s TelegramPlatform starting')
        self._telegram_app.run_polling()
        loop.close()

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
            handler (:obj:`telegram.ext.BaseHandler`): the handler to add
        """
        self._telegram_app.add_handler(handler)
