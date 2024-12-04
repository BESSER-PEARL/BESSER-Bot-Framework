"""
The collection of preexisting intents.
"""

from besser.agent.core.intent.intent import Intent

fallback_intent = Intent(name='fallback_intent')
"""The Fallback Intent. Used when no intent is matched by the Intent Classifier."""
