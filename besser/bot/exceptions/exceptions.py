class StateNotFound(Exception):

    def __init__(self, bot, state):
        message = f"State '{state.name}' not found in bot '{bot.name}'"
        super().__init__(message)


class IntentNotFound(Exception):

    def __init__(self, bot, intent):
        message = f"Intent '{intent.name}' not found in bot '{bot.name}'"
        super().__init__(message)


class DuplicatedIntentError(Exception):

    def __init__(self, bot, intent):
        message = f"Bot '{bot.name}' already contains an intent with name '{intent.name}'"
        super().__init__(message)


class DuplicatedStateError(Exception):

    def __init__(self, bot, state):
        message = f"Bot '{bot.name}' already contains a state with name '{state.name}'"
        super().__init__(message)


class DuplicatedEntityError(Exception):

    def __init__(self, bot, entity):
        message = f"Bot '{bot.name}' already contains an entity with name '{entity.name}'"
        super().__init__(message)


class DuplicatedIntentMatchingTransitionError(Exception):

    def __init__(self, state, intent):
        message = f"State '{state.name}' already contains an transition for when intent '{intent.name}' is matched"
        super().__init__(message)


class DuplicatedInitialStateError(Exception):

    def __init__(self, bot, initial_state1, initial_state2):
        message = f"Bot '{bot.name}' already contains an initial state '{initial_state1.name}', and " \
                  f"'{initial_state2.name}' cannot be initial"
        super().__init__(message)


class InitialStateNotFound(Exception):

    def __init__(self, bot):
        message = f"Bot '{bot.name}' could not be deployed because it has no initial state"
        super().__init__(message)


class BodySignatureError(Exception):

    def __init__(self, bot, state, body, body_template_signature, body_signature):
        message = f"Expected parameters in body method '{body.__name__}' of state '{state.name}' in bot '{bot.name}' " \
                  f"are {body_template_signature}, got {body_signature} instead"
        super().__init__(message)


class DuplicatedAutoTransitionError(Exception):

    def __init__(self, bot, state):
        message = f"State '{state.name}' in bot '{bot.name}' cannot contain more than 1 auto transition " \
                  f"({state.go_to.__name__}() call)"
        super().__init__(message)


class PlatformMismatchError(Exception):

    def __init__(self, platform, session):
        message = f"Attempting to reply with platform {platform.__class__.__name__} in a session with platform " \
                  f"{session.platform.__class__.__name__}. Please use the appropriate platform for this session"
        super().__init__(message)


class IntentClassifierWithoutIntentsError(Exception):

    def __init__(self, state, intent_classifier):
        message = f"Attempting to create a {intent_classifier.__class__.__name__} in a state without intents: " \
                  f"{state.name}"
        super().__init__(message)
