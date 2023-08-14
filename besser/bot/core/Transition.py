from besser.bot.library.event.EventLibrary import intent_matched, auto
from besser.bot.core.intent.Intent import Intent


class Transition:

    def __init__(self, name, source, dest, event, event_params):
        self.name = name
        self.source = source
        self.dest = dest
        self.event = event
        self.event_params = event_params

    def log(self):
        if self.event == intent_matched:
            return f"{self.event.__name__} ({self.event_params['intent'].name}): [{self.source.name}] --> " \
                   f"[{self.dest.name}]"
        elif self.event == auto:
            return f"{self.event.__name__}: [{self.source.name}] --> [{self.dest.name}]"

    def is_intent_matched(self, intent: Intent):
        if self.event == intent_matched:
            target_intent = self.event_params['intent']
            return self.event(target_intent, intent)
        return False

    def is_auto(self):
        return self.event == auto

    def check(self, obj: object):
        if self.event == intent_matched and isinstance(obj, Intent):
            target_intent = self.event_params['intent']
            return self.event(target_intent, obj)
        return False
