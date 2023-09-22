from besser.bot.core.property import Property

# Definition of the bot properties within the telegram_platform section

SECTION_TELEGRAM = 'telegram_platform'

TELEGRAM_TOKEN = Property(SECTION_TELEGRAM, 'telegram.token', str, None)
