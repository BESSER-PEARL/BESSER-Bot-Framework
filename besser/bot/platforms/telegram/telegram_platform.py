import asyncio
import base64
import logging
import threading
from concurrent.futures import Future
from datetime import datetime
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, BaseHandler, CommandHandler, ContextTypes, MessageHandler, \
    filters

from besser.bot.core.message import Message, MessageType
from besser.bot.core.session import Session
from besser.bot.core.file import File
from besser.bot.exceptions.exceptions import PlatformMismatchError
from besser.bot.platforms import telegram
from besser.bot.platforms.payload import Payload, PayloadAction
from besser.bot.platforms.platform import Platform

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


def _wait_future(future: Future):
    """
    Wait for a future (an asynchronous coroutine) to be finished.

    Args:
        future (Future): the Future to wait for
    """
    event = threading.Event()
    future.add_done_callback((lambda ft: event.set()))
    event.wait()


class TelegramPlatform(Platform):
    """The Telegram Platform allows a bot to interact via Telegram.

    It includes a `message handler` to handle all text inputs except commands (i.e. messages starting with '/'),
    `voice`, `file` and `image` handlers and a `reset handler`, triggered by the `/reset` command, to reset the bot
    session.

    Args:
        bot (Bot): the bot the platform belongs to

    Attributes:
        _bot (Bot): The bot the platform belongs to
        _telegram_app (telegram.ext.Application): The Telegram Application
        _event_loop (asyncio.AbstractEventLoop): The event loop that runs the asynchronous tasks of the Telegram
            Application
        _handlers (list[telegram.ext.BaseHandler]): List of telegram bot handlers
    """
    def __init__(self, bot: 'Bot'):
        super().__init__()
        self._bot: 'Bot' = bot
        self._telegram_app: Application = None
        self._event_loop: asyncio.AbstractEventLoop = None
        self._handlers: list[BaseHandler] = []

        # Handler for text messages
        async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            session = await asyncio.to_thread(self._bot.get_or_create_session, session_id, self)
            text = update.message.text
            await asyncio.to_thread(self._bot.receive_message, session.id, text)

        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message, block=False)
        self._handlers.append(message_handler)

        # Handler for reset command
        async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            await asyncio.to_thread(self._bot.reset, session_id)

        reset_handler = CommandHandler('reset', reset, block=False)
        self._handlers.append(reset_handler)

        # Handler for voice messages
        async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            session = await asyncio.to_thread(self._bot.get_or_create_session, session_id, self)
            voice_file = await context.bot.get_file(update.message.voice.file_id)
            voice_data = await voice_file.download_as_bytearray()
            text = self._bot.nlp_engine.speech2text(bytes(voice_data))
            await asyncio.to_thread(self._bot.receive_message, session.id, text)

        voice_handler = MessageHandler(filters.VOICE, voice, block=False)
        self._handlers.append(voice_handler)

        # Handler for file messages
        async def file(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            session = await asyncio.to_thread(self._bot.get_or_create_session, session_id, self)
            file_object = await context.bot.get_file(update.message.document.file_id)
            file_data = await file_object.download_as_bytearray()
            base64_data = base64.b64encode(file_data).decode()
            f = File(
                file_name=update.message.document.file_name, file_type=update.message.document.mime_type,
                file_base64=base64_data
            )
            await asyncio.to_thread(self._bot.receive_file, session.id, file=f)

        file_handler = MessageHandler(filters.ATTACHMENT & (~filters.PHOTO), file, block=False)
        self._handlers.append(file_handler)

        # Handler for image messages
        async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session_id = str(update.effective_chat.id)
            session = await asyncio.to_thread(self._bot.get_or_create_session, session_id, self)
            image_object = await context.bot.get_file(update.message.photo[-1].file_id)
            image_data = await image_object.download_as_bytearray()
            base64_data = base64.b64encode(image_data).decode()
            f = File(
                file_name=update.message.photo[-1].file_id + ".jpg", file_type="image/jpeg",
                file_base64=base64_data
            )
            await asyncio.to_thread(self._bot.receive_file, session.id, file=f)

        image_handler = MessageHandler(filters.PHOTO, image, block=False)
        self._handlers.append(image_handler)

    def __getattr__(self, name: str):
        """All methods in :class:`telegram.ext._extbot.ExtBot` (that extends :class:`telegram._bot.Bot`) can be used
        from the TelegramPlatform.

        Args:
            name (str): the name of the function to call
        """
        def method_proxy(*args, **kwargs):
            # Forward the method call to the (telegram) bot
            method = getattr(self._telegram_app.bot, name, None)
            if method:
                future = asyncio.run_coroutine_threadsafe(method(*args, **kwargs), self._event_loop)
                _wait_future(future)
                return future.result()
            else:
                raise AttributeError(f"'{self._telegram_app.bot.__class__}' object has no attribute '{name}'")
        return method_proxy

    @property
    def telegram_app(self):
        """telegram.ext._application.Application: The Telegram app."""
        return self._telegram_app

    def initialize(self) -> None:
        # Hide Info logging messages
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self._telegram_app = ApplicationBuilder().token(
            self._bot.get_property(telegram.TELEGRAM_TOKEN)).concurrent_updates(True).build()
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
        session = self._bot.get_or_create_session(session_id=session_id, platform=self)
        payload.message = self._bot.process(is_user_message=False, session=session, message=payload.message)
        if payload.action == PayloadAction.BOT_REPLY_STR.value:
            future = asyncio.run_coroutine_threadsafe(
                self._telegram_app.bot.send_message(
                    chat_id=session_id,
                    text=payload.message
                ),
                self._event_loop
            )
        elif payload.action == PayloadAction.BOT_REPLY_FILE.value:
            future = asyncio.run_coroutine_threadsafe(
                self._telegram_app.bot.send_document(
                    chat_id=session_id,
                    document=base64.b64decode(payload.message["base64"]),
                    filename=payload.message["name"],
                    caption=payload.message["caption"]
                ),
                self._event_loop
            )
        elif payload.action == PayloadAction.BOT_REPLY_IMAGE.value:
            future = asyncio.run_coroutine_threadsafe(
                self._telegram_app.bot.send_photo(
                    chat_id=session_id,
                    photo=base64.b64decode(payload.message["base64"]),
                    caption=payload.message["caption"]
                ),
                self._event_loop
            )
        elif payload.action == PayloadAction.BOT_REPLY_LOCATION.value:
            future = asyncio.run_coroutine_threadsafe(
                self._telegram_app.bot.send_location(
                    chat_id=session_id,
                    latitude=payload.message['latitude'],
                    longitude=payload.message['longitude'],
                ),
                self._event_loop
            )
        else:
            future = None
        if future is not None:
            _wait_future(future)

    def reply(self, session: Session, message: str) -> None:
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.save_message(Message(t=MessageType.STR, content=message, is_user=False, timestamp=datetime.now()))
        payload = Payload(action=PayloadAction.BOT_REPLY_STR,
                          message=message)
        self._send(session.id, payload)

    def reply_file(self, session: Session, file: File, message: str = None) -> None:
        """Send a file reply to a specific user

        Args:
            session (Session): the user session
            file (File): the file to send
            message (str, optional): message to be attached to file, 1024 char limit
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.save_message(Message(t=MessageType.FILE, content=file.get_json_string(), is_user=False, timestamp=datetime.now()))
        file_dict = file.to_dict()
        if message:
            file_dict["caption"] = message
        else:
            file_dict["caption"] = ""
        payload = Payload(action=PayloadAction.BOT_REPLY_FILE,
                          message=file_dict)
        self._send(session.id, payload)

    def reply_image(self, session: Session, file: File, message: str = None) -> None:
        """Send an image reply to a specific user

        Args:
            session (Session): the user session
            file (File): the file to send (the image)
            message (str, optional): message to be attached to file, 1024 char limit
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.save_message(Message(t=MessageType.IMAGE, content=file.get_json_string(), is_user=False, timestamp=datetime.now()))
        file_dict = file.to_dict()
        if message:
            file_dict["caption"] = message
        else:
            file_dict["caption"] = ""
        payload = Payload(action=PayloadAction.BOT_REPLY_IMAGE,
                          message=file_dict)
        self._send(session.id, payload)

    def reply_location(self, session: Session, latitude: float, longitude: float) -> None:
        """Send a location reply to a specific user.

        Args:
            session (Session): the user session
            latitude (str): the latitude of the location
            longitude (str): the longitude of the location
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        location_dict = {'latitude': latitude, 'longitude': longitude}
        session.save_message(Message(t=MessageType.LOCATION, content=location_dict, is_user=False, timestamp=datetime.now()))
        payload = Payload(action=PayloadAction.BOT_REPLY_LOCATION,
                          message=location_dict)
        self._send(session.id, payload)

    def add_handler(self, handler: BaseHandler) -> None:
        """
        Add a custom Telegram handler for the bot.

        Args:
            handler (telegram.ext.BaseHandler): the handler to add
        """
        self._handlers.append(handler)
