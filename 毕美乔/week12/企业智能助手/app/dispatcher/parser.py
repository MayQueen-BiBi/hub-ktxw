from .intent import Intent


def parse_intent(raw_intent: str | None) -> Intent:
    if not raw_intent:
        return Intent.CHAT

    try:
        return Intent(raw_intent.lower())
    except ValueError:
        return Intent.CHAT
