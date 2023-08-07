from besser.bot.core.Session import Session


def body_template(session: Session):
    pass


def default_fallback_body(session: Session):
    session.reply("Greetings from default fallback")
