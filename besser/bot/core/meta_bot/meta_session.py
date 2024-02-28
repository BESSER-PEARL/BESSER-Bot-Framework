from besser.bot.core.bot import Bot
from besser.bot.core.session import Session
from besser.bot.platforms.platform import Platform


class MetaSession(Session):

    def __init__(
            self,
            session_id: str,
            metabot: 'MetaBot',
            platform: Platform,
    ):
        super().__init__(session_id, metabot, platform)
        self._bot: 'MetaBot' = metabot
        self._current_bot: Bot or None = None

    def get_bot(self, name: str):
        return self._bot.get_bot(name)