import logging
import random

from besser.bot.core.Bot import Bot
from besser.bot.core.Session import Session
from besser.bot.nlp.intent_classifier.IntentClassifierPrediction import IntentClassifierPrediction

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

bot = Bot('greetings-bot')
bot.load_properties('config.properties')


def global_fallback_body(session: Session):
    session.reply("Greetings from global fallback")


# Assigned to all bot states (overriding all currently assigned fallback bodies).
# In this case, it replaces besser.bot.library.state.StateLibrary.default_fallback_body
bot.set_global_fallback_body(global_fallback_body)

# STATES

s0 = bot.new_state('s0', initial=True)
hello_state = bot.new_state('hello_state')
bye_state = bot.new_state('bye_state')
weather_state = bot.new_state('weather_state')

# ENTITIES

city_entity = bot.new_entity('city_entity', entries={
    'Barcelona': ['BCN', 'barna'],
    'Madrid': ['MAD']
})

# INTENTS

hello_intent = bot.new_intent('hello_intent', [
    'hello',
    'hi',
    'how are you?'
])

bye_intent = bot.new_intent('bye_intent', [
    'bye',
    'goodbye',
    'see you'
])

weather_intent = bot.new_intent('weather_intent', [
    'weather',
    'weather in CITY',
])
weather_intent.parameter('city1', 'CITY1', city_entity)

# GLOBAL VARIABLES

count_hello = 0
count_bye = 0

# STATES BODIES' DEFINITION + TRANSITIONS


def s0_body(session: Session):
    session.reply('Waiting...')


s0.set_body(s0_body)

s0.when_intent_matched_go_to(hello_intent, hello_state)
s0.when_intent_matched_go_to(bye_intent, bye_state)
s0.when_intent_matched_go_to(weather_intent, weather_state)


def hello_body(session: Session):
    global count_hello
    count_hello = count_hello + 1
    session.reply('You said hello ' + str(count_hello) + ' times')


# Custom fallback for hello_state
def hello_fallback_body(session: Session):
    session.reply("Greetings from hello fallback")


hello_state.set_body(hello_body)
hello_state.set_fallback_body(hello_fallback_body)

hello_state.when_intent_matched_go_to(bye_intent, bye_state)
# hello_state.go_to(s0)  # This transition will be triggered when no intent is detected, replacing the fallback scenario


def bye_body(session: Session):
    global count_bye
    count_bye = count_bye + 1
    session.reply('You said bye ' + str(count_bye) + ' times')


bye_state.set_body(bye_body)
bye_state.go_to(s0)


def weather_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.get_predicted_intent()
    city = predicted_intent.get_parameter('city1')
    if city.value is None:
        session.reply("Sorry, I didn't get the city")
    else:
        session.reply(f"The weather in {city.value} is {random.uniform(0, 30)}")


weather_state.set_body(weather_body)
weather_state.go_to(s0)

# RUN APPLICATION

if __name__ == '__main__':
    bot.run(use_ui=True)
