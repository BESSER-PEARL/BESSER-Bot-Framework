class AgentNotTrainedError(Exception):

    def __init__(self, agent):
        message = f"Attempting to run the agent '{agent.name}', which has not been trained. Run Agent.train() or " \
                  f"Agent.run(train=True)"
        super().__init__(message)


class StateNotFound(Exception):

    def __init__(self, agent, state):
        message = f"State '{state.name}' not found in agent '{agent.name}'"
        super().__init__(message)


class IntentNotFound(Exception):

    def __init__(self, agent, intent):
        message = f"Intent '{intent.name}' not found in agent '{agent.name}'"
        super().__init__(message)


class DuplicatedIntentError(Exception):

    def __init__(self, agent, intent):
        message = f"Agent '{agent.name}' already contains an intent with name '{intent.name}'"
        super().__init__(message)


class DuplicatedStateError(Exception):

    def __init__(self, agent, state):
        message = f"Agent '{agent.name}' already contains a state with name '{state.name}'"
        super().__init__(message)


class DuplicatedEntityError(Exception):

    def __init__(self, agent, entity):
        message = f"Agent '{agent.name}' already contains an entity with name '{entity.name}'"
        super().__init__(message)


class DuplicatedIntentParameterError(Exception):

    def __init__(self, intent, name):
        message = f"Intent '{intent.name}' already contains a parameter with name '{name}'"
        super().__init__(message)


class DuplicatedIntentMatchingTransitionError(Exception):

    def __init__(self, state, intent):
        message = f"State '{state.name}' already contains an transition for when intent '{intent.name}' is matched"
        super().__init__(message)


class DuplicatedInitialStateError(Exception):

    def __init__(self, agent, initial_state1, initial_state2):
        message = f"Agent '{agent.name}' already contains an initial state '{initial_state1.name}', and " \
                  f"'{initial_state2.name}' cannot be initial"
        super().__init__(message)


class InitialStateNotFound(Exception):

    def __init__(self, agent):
        message = f"Agent '{agent.name}' could not be deployed because it has no initial state"
        super().__init__(message)


class BodySignatureError(Exception):

    def __init__(self, agent, state, body, body_template_signature, body_signature):
        message = f"Expected parameters in body method '{body.__name__}' of state '{state.name}' in agent '{agent.name}' " \
                  f"are {body_template_signature}, got {body_signature} instead"
        super().__init__(message)


class EventSignatureError(Exception):

    def __init__(self, agent, event, event_template_signature, event_signature):
        message = f"Expected parameters in event method '{event.__name__}' in agent " \
                  f"'{agent.name}' are {event_template_signature}, got {event_signature} instead"
        super().__init__(message)


class DuplicatedAutoTransitionError(Exception):

    def __init__(self, agent, state):
        message = f"State '{state.name}' in agent '{agent.name}' cannot contain more than 1 auto transition " \
                  f"({state.go_to.__name__}() call)"
        super().__init__(message)


class ConflictingAutoTransitionError(Exception):

    def __init__(self, agent, state):
        message = f"State '{state.name}' in agent '{agent.name}' cannot contain an auto transition with other transitions " \
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


class SREngineNotFound(Exception):

    def __init__(self, engine, engines):
        message = f"Chosen speech recognition engine \"{engine}\" is not supported, choose one of the following: \n"
        for engine in engines:
            message += engine + "\n"
        super().__init__(message)


class ProcessorTargetUndefined(Exception):
    def __init__(self, processor):
        message = (f"The processor {processor.__class__.__name__} was not configured correctly, you need to specify " \
                   f"which message needs to be processed. Reminder: Either \"user_messages\" or \"agent_messages\" (or " \
                   f"both) need to be set to true.\n")
        super().__init__(message)
