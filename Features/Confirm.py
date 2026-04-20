AFFIRMATIVE = [
    "yes",
    "yeah",
    "yep",
    "ok",
    "okay",
    "sure",
    "do it",
    "go ahead",
    "please",
    "send it",
    "send",
    "go for it",
    "sounds good",
    "yes do it",
]

NEGATIVE = [
    "no",
    "nope",
    "stop",
    "cancel",
    "don't",
    "do not",
    "not now",
    "not yet",
]


def is_affirmative(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(p in t for p in AFFIRMATIVE)


def is_negative(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(p in t for p in NEGATIVE)


def ask_yes_no(prompt: str) -> bool:
    from Features.Face.Ear import understand
    from Features.Face.Mouth import speak
    speak(prompt)
    while True:
        reply = understand()
        if is_affirmative(reply):
            return True
        if is_negative(reply):
            return False
        speak("Please say yes or no.")
