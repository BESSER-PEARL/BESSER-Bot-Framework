import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, BaseHandler, CommandHandler, ContextTypes, MessageHandler, filters

from besser.bot.core.Session import Session
from besser.bot.exceptions.exceptions import PlatformMismatchError
from besser.bot.platforms.Payload import Payload
from besser.bot.platforms.Platform import Platform


class TelegramPlatform(Platform):

    def __init__(self, bot):
        super.__init__()
        self.bot = bot
        self.telegram_app = ApplicationBuilder().token(self.bot.config.get('telegram', 'token', fallback=None)).build()

        # Handler for text messages
        async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = update.effective_chat.id
            if session_id in self.bot.sessions:
                text = update.message.text
                self.bot.receive_message(session_id, text)
            else:
                self.bot.new_session(update.effective_chat.id, self)
        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
        self.telegram_app.add_handler(message_handler)

        # Handler for reset command
        async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
            self.bot.reset(update.effective_chat.id)
        reset_handler = CommandHandler('reset', reset)
        self.telegram_app.add_handler(reset_handler)



    def run(self):
        logging.getLogger("httpx").setLevel(logging.WARNING)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logging.info(f'{self.bot.name}\'s TelegramPlatform starting')
        self.telegram_app.run_polling()
        loop.close()

    def _send(self, session_id, payload: Payload):
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(self.telegram_app.bot.send_message(chat_id=session_id, text=payload.message),
                                         loop)

    def reply(self, session: Session, message: str):
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.chat_history.append((message, 0))
        payload = Payload(action=Payload.BOT_REPLY_STR,
                          message=message)
        self._send(session.id, payload)

    def add_handler(self, handler: BaseHandler):
        self.telegram_app.add_handler(handler)
