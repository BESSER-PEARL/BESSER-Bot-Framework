from besser.bot.core.session import Session


def default_body(session: Session):
    pass


def default_fallback_body(session: Session):
    session.reply("Sorry, I didn't get it")
