from besser.bot.core.intent import Intent


def auto():
    return True


def intent_matched(target_intent: Intent, matched_intent: Intent):
    return target_intent.name == matched_intent.name
