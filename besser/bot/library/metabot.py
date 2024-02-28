from besser.bot.core.bot import Bot
from besser.bot.core.meta_bot.meta_session import MetaSession
from besser.bot.core.session import Session


def default_body_metabot(session: MetaSession) -> None:
    """
    The default body of a MetaBot. Does nothing.

    Used when no body is defined in a MetaBot.

    Used as a reference for bodies method signatures.

    Args:
        session (MetaSession): the current user session
    """
    pass


def default_fallback_body_metabot(session: MetaSession) -> None:
    """
    The default fallback body of a MetaBot.

    Used when no fallback body is defined in a MetaBot.

    Used as a reference for fallback bodies method signatures.

    Args:
        session (MetaSession): the current user session
    """
    session.reply("Sorry, Meta Bot not able to identify bot")


def default_bot_prediction(session: MetaSession, message: str) -> Bot:
    pass


def default_after_bot_prediction(metabot_session: MetaSession, bot_session: Session) -> None:
    pass
