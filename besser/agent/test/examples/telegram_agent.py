# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

agent = Agent('telegram_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
telegram_platform = agent.use_telegram_platform()


# Adding a custom handler for the Telegram Application: command /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = agent.get_or_create_session(str(update.effective_chat.id), telegram_platform)
    session.reply('I am an agent, tell me something!')
help_handler = CommandHandler('help', help)
telegram_platform.add_handler(help_handler)


# STATES

s0 = agent.new_state('s0', initial=True)
hello_state = agent.new_state('hello_state')
bye_state = agent.new_state('bye_state')
howareyou_state = agent.new_state('howareyou_state')

# INTENTS

hello_intent = agent.new_intent('hello_intent', [
    'hello',
    'hi'
])

bye_intent = agent.new_intent('bye_intent', [
    'bye',
    'goodbye',
    'see you'
])

howareyou_intent = agent.new_intent('howareyou_intent', [
    'how are you?',
    'how r u',
])

# GLOBAL VARIABLES

count_hello = 0
count_bye = 0

# STATES BODIES' DEFINITION + TRANSITIONS


def global_fallback_body(session: Session):
    telegram_platform.reply(session, 'Greetings from global fallback')


# Assigned to all agent states (overriding all currently assigned fallback bodies).
agent.set_global_fallback_body(global_fallback_body)


def s0_body(session: Session):
    telegram_platform.reply(session, 'Waiting...')


s0.set_body(s0_body)
s0.when_intent_matched_go_to(hello_intent, hello_state)
s0.when_intent_matched_go_to(howareyou_intent, howareyou_state)


def hello_body(session: Session):
    global count_hello
    count_hello = count_hello + 1
    telegram_platform.reply(session, f'You said hello {count_hello} times')


# Custom fallback for hello_state
def hello_fallback_body(session: Session):
    telegram_platform.reply(session, 'Greetings from hello fallback')


hello_state.set_body(hello_body)
hello_state.set_fallback_body(hello_fallback_body)
hello_state.when_intent_matched_go_to(bye_intent, bye_state)


def bye_body(session: Session):
    global count_bye
    count_bye = count_bye + 1
    telegram_platform.reply(session, f'You said bye {count_bye} times')


bye_state.set_body(bye_body)
bye_state.go_to(s0)


def howareyou_body(session: Session):
    telegram_platform.reply(session, f'I am fine, thanks!')


howareyou_state.set_body(howareyou_body)
howareyou_state.go_to(s0)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
