"""Definition of the bot properties within the ``telegram_platform`` section:"""

from besser.bot.core.property import Property

SECTION_TELEGRAM = 'telegram_platform'

TELEGRAM_TOKEN = Property(SECTION_TELEGRAM, 'telegram.token', str, None)
"""
The Telegram Bot token. Used to connect to the Telegram Bot

type: ``str``

default value: ``None``
"""
