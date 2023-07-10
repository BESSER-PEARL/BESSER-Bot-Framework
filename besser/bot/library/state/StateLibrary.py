from besser.bot.core.Session import Session


def body_template(session: Session):
    pass


def default_fallback_body(session: Session):
    session.put_answer("Greetings from default fallback")
