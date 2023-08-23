import logging

from besser.bot.core.bot import Bot
from besser.bot.core.session import Session

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

# Create the bot
bot = Bot('greetings_bot')
# Load bot properties stored in a dedicated file
bot.load_properties('config.ini')
# Define the platform your chatbot will use
websocket_platform = bot.use_websocket_platform(use_ui=True)

# STATES

s0 = bot.new_state('s0', initial=True)
hello_state = bot.new_state('hello_state')
bye_state = bot.new_state('bye_state')

# INTENTS

hello_intent = bot.new_intent('hello_intent', [
    'hello',
    'hi'
])

bye_intent = bot.new_intent('bye_intent', [
    'bye',
    'goodbye',
    'see you'
])


# STATES BODIES' DEFINITION + TRANSITIONS


def s0_body(session: Session):
    session.reply('Hello!')


s0.set_body(s0_body)
s0.when_intent_matched_go_to(hello_intent, hello_state)


def hello_body(session: Session):
    session.reply('Bye!')


hello_state.set_body(hello_body)
hello_state.when_intent_matched_go_to(bye_intent, bye_state)


def bye_body(session: Session):
    session.reply('Let\'s start again...')


bye_state.set_body(bye_body)
bye_state.go_to(s0)


# RUN APPLICATION

if __name__ == '__main__':
    bot.run()
